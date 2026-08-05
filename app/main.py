import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.models.registry import (
    has_model,
    list_models,
    list_model_versions,
    model_metadata,
    promote_model_version,
    register_model_version,
    resolve_model_version,
)
from app.audit import list_admin_audit_events, record_admin_audit_event
from app.monitoring import DriftMonitor
from app.queue.redis_queue import (
    dead_letter_depth,
    enqueue_job,
    get_idempotency_job,
    get_job,
    ping,
    queue_depth,
    set_idempotency_job,
    set_job,
)
from app.observability import (
    log_event,
    metrics_payload,
    set_dead_letter_depth,
    set_queue_depth,
    track_http_metrics,
    track_job_status,
)
from app.security import allow_request, verify_api_key
from app.security import verify_admin_key

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 5 * 1024 * 1024))
DEFAULT_JOB_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_JOB_TIMEOUT_SECONDS", 60))
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXEMPT_PATHS = {"/health", "/ready", "/metrics"}
ADMIN_PATHS = {"/models/register", "/admin/audit"}

app = FastAPI(title="VisionFlow")
DRIFT_MONITOR = DriftMonitor()


class RegisterModelVersionRequest(BaseModel):
    model: str
    version: str
    runtime: str
    artifact_uri: str
    class_path: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    resources: dict[str, Any]


class PromoteModelVersionRequest(BaseModel):
    version: str


class DriftBaselineRequest(BaseModel):
    baseline: dict[str, dict[str, float]]


class DriftObserveRequest(BaseModel):
    features: dict[str, float]
    label: str | None = None


class AuditEventListResponse(BaseModel):
    events: list[dict[str, Any]]


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def now_utc_epoch():
    return datetime.now(timezone.utc).timestamp()


def trace_id_from_request(request: Request):
    return getattr(request.state, "trace_id", "unknown")


def error_payload(code: str, message: str, details: dict[str, Any], trace_id: str):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "trace_id": trace_id,
        }
    }


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start_time = datetime.now().timestamp()
    request.state.trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))

    if request.url.path not in EXEMPT_PATHS:
        api_key = request.headers.get("X-API-Key")
        if not verify_api_key(api_key):
            response = JSONResponse(
                status_code=401,
                content=error_payload(
                    code="unauthorized",
                    message="Missing or invalid API key",
                    details={"header": "X-API-Key"},
                    trace_id=request.state.trace_id,
                ),
            )
            response.headers["X-Trace-Id"] = request.state.trace_id
            track_http_metrics(request.method, request.url.path, 401, start_time)
            return response

        client_id = api_key or (request.client.host if request.client else "unknown")
        if not allow_request(client_id):
            response = JSONResponse(
                status_code=429,
                content=error_payload(
                    code="rate_limited",
                    message="Rate limit exceeded",
                    details={},
                    trace_id=request.state.trace_id,
                ),
            )
            response.headers["X-Trace-Id"] = request.state.trace_id
            track_http_metrics(request.method, request.url.path, 429, start_time)
            return response

        if request.url.path in ADMIN_PATHS or (
            request.url.path.startswith("/models/") and request.url.path.endswith("/promote")
        ):
            admin_key = request.headers.get("X-Admin-Key")
            if not verify_admin_key(admin_key):
                response = JSONResponse(
                    status_code=403,
                    content=error_payload(
                        code="forbidden",
                        message="Missing or invalid admin API key",
                        details={"header": "X-Admin-Key"},
                        trace_id=request.state.trace_id,
                    ),
                )
                response.headers["X-Trace-Id"] = request.state.trace_id
                track_http_metrics(request.method, request.url.path, 403, start_time)
                return response

    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    track_http_metrics(request.method, request.url.path, response.status_code, start_time)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    details = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            code="http_error",
            message="Request failed",
            details=details,
            trace_id=trace_id_from_request(request),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_payload(
            code="validation_error",
            message="Validation failed",
            details={"errors": exc.errors()},
            trace_id=trace_id_from_request(request),
        ),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=error_payload(
            code="internal_error",
            message="Unexpected server error",
            details={"exception": str(exc)},
            trace_id=trace_id_from_request(request),
        ),
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        redis_ok = ping()
        q_depth = queue_depth()
        dlq_depth = dead_letter_depth()
    except Exception:
        redis_ok = False
        q_depth = 0
        dlq_depth = 0
    set_queue_depth(q_depth)
    set_dead_letter_depth(dlq_depth)
    return {
        "status": "ok" if redis_ok else "degraded",
        "dependencies": {"redis": "ok" if redis_ok else "down"},
        "queue_depth": q_depth,
        "dead_letter_depth": dlq_depth,
    }


@app.get("/metrics")
def metrics():
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)


@app.get("/models")
def available_models():
    models = list_models()
    return {
        "available_models": models,
        "models": [
            {
                "name": model,
                "default_version": model_metadata(model)["default_version"],
                "versions": list_model_versions(model),
            }
            for model in models
        ],
    }


@app.get("/models/{model_name}/versions")
def model_versions(model_name: str):
    if not has_model(model_name):
        raise HTTPException(status_code=404, detail={"model": model_name, "reason": "Unknown model"})
    return {
        "model": model_name,
        "default_version": model_metadata(model_name)["default_version"],
        "versions": [model_metadata(model_name, version) for version in list_model_versions(model_name)],
    }


@app.post("/models/register")
def register_model(request: Request, payload: RegisterModelVersionRequest):
    if payload.runtime != "onnx":
        raise HTTPException(
            status_code=400,
            detail={"runtime": payload.runtime, "reason": "Only 'onnx' runtime is currently supported"},
        )
    if "." not in payload.class_path:
        raise HTTPException(
            status_code=400,
            detail={"class_path": payload.class_path, "reason": "class_path must be fully qualified"},
        )
    registry_payload = {
        "runtime": payload.runtime,
        "artifact_uri": payload.artifact_uri,
        "class": payload.class_path,
        "input_schema": payload.input_schema,
        "output_schema": payload.output_schema,
        "resources": payload.resources,
    }
    try:
        register_model_version(payload.model, payload.version, registry_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"reason": str(exc)})
    record_admin_audit_event(
        "model_registered",
        trace_id=trace_id_from_request(request),
        model=payload.model,
        version=payload.version,
        runtime=payload.runtime,
    )
    log_event("model_registered", model=payload.model, version=payload.version, runtime=payload.runtime)
    return {"status": "registered", "model": payload.model, "version": payload.version}


@app.post("/models/{model_name}/promote")
def promote_model(model_name: str, request: Request, payload: PromoteModelVersionRequest):
    try:
        promote_model_version(model_name, payload.version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"reason": str(exc)})
    record_admin_audit_event(
        "model_promoted",
        trace_id=trace_id_from_request(request),
        model=model_name,
        version=payload.version,
    )
    log_event("model_promoted", model=model_name, version=payload.version)
    return {"status": "promoted", "model": model_name, "default_version": payload.version}


@app.get("/admin/audit", response_model=AuditEventListResponse)
def admin_audit(limit: int = 50):
    return {"events": list_admin_audit_events(limit=limit)}


@app.post("/monitoring/drift/baseline")
def set_drift_baseline(request: DriftBaselineRequest):
    DRIFT_MONITOR.set_baseline(request.baseline)
    return {"status": "baseline_set", "features": sorted(request.baseline.keys())}


@app.post("/monitoring/drift/observe")
def observe_drift(request: DriftObserveRequest):
    DRIFT_MONITOR.observe_features(request.features)
    if request.label is not None:
        DRIFT_MONITOR.observe_prediction(request.label)
    return {"status": "observed"}


@app.get("/monitoring/drift/summary")
def drift_summary():
    return DRIFT_MONITOR.summary()


@app.post("/predict")
async def predict(
    request: Request,
    model: str = Form(...),
    model_version: str | None = Form(default=None),
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _predict_impl(
        request=request,
        model=model,
        model_version=model_version,
        files=[file],
        idempotency_key=idempotency_key,
        batch_mode=False,
    )


@app.post("/predict/batch")
async def predict_batch(
    request: Request,
    model: str = Form(...),
    model_version: str | None = Form(default=None),
    files: list[UploadFile] = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return await _predict_impl(
        request=request,
        model=model,
        model_version=model_version,
        files=files,
        idempotency_key=idempotency_key,
        batch_mode=True,
    )


async def _predict_impl(
    request: Request,
    model: str,
    model_version: str | None,
    files: list[UploadFile],
    idempotency_key: str | None,
    batch_mode: bool,
):
    if not has_model(model, model_version):
        raise HTTPException(
            status_code=400,
            detail={"model": model, "model_version": model_version, "reason": "Unknown model/version"},
        )

    if batch_mode and not files:
        raise HTTPException(status_code=400, detail={"reason": "At least one file is required"})

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail={"content_type": file.content_type, "allowed": sorted(ALLOWED_IMAGE_MIME_TYPES)},
            )

    resolved_version = resolve_model_version(model, model_version)

    if idempotency_key:
        existing_job_id = get_idempotency_job(idempotency_key)
        if existing_job_id:
            existing = get_job(existing_job_id)
            if existing is not None:
                return {
                    "job_id": existing_job_id,
                    "model": existing["model"],
                    "model_version": existing["model_version"],
                    "status": existing["status"],
                    "idempotency_reused": True,
                }

    image_bytes_list = [await file.read() for file in files]
    total_bytes = sum(len(image_bytes) for image_bytes in image_bytes_list)
    for image_bytes in image_bytes_list:
        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail={"max_upload_bytes": MAX_UPLOAD_BYTES, "received_bytes": len(image_bytes)},
            )

    job_id = str(uuid.uuid4())
    created_at = now_utc_iso()
    created_at_epoch = now_utc_epoch()
    job_payload = {
        "job_id": job_id,
        "status": "queued",
        "model": model,
        "model_version": resolved_version,
        "created_at": created_at,
        "created_at_epoch": created_at_epoch,
        "updated_at": created_at,
        "duration_ms": None,
        "attempt": 0,
        "max_retries": 3,
        "timeout_seconds": DEFAULT_JOB_TIMEOUT_SECONDS,
        "cancel_requested": False,
        "error_code": None,
        "batch_count": len(image_bytes_list),
        "batch_total_bytes": total_bytes,
        "result": None,
        "error": None,
    }
    if batch_mode:
        job_payload["image_bytes_list"] = [image_bytes.hex() for image_bytes in image_bytes_list]
    else:
        job_payload["image_bytes"] = image_bytes_list[0].hex()

    set_job(job_id, job_payload)

    if idempotency_key:
        set_idempotency_job(idempotency_key, job_id)

    enqueue_job(job_id)
    track_job_status("queued", model, resolved_version)
    log_event(
        "job_enqueued",
        trace_id=trace_id_from_request(request),
        job_id=job_id,
        model=model,
        model_version=resolved_version,
    )

    return {
        "job_id": job_id,
        "model": model,
        "model_version": resolved_version,
        "batch_count": len(image_bytes_list),
        "status": "queued",
        "idempotency_reused": False,
    }


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail={"job_id": job_id, "reason": "Job not found"})

    response = {k: v for k, v in job.items() if k not in {"image_bytes", "image_bytes_list"}}
    log_event(
        "job_status_read",
        job_id=job_id,
        status=response.get("status"),
        model=response.get("model"),
        model_version=response.get("model_version"),
    )
    return response


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"job_id": job_id, "reason": "Job not found"})
    if job["status"] in {"completed", "failed", "timed_out", "dead_lettered"}:
        return {"job_id": job_id, "status": job["status"], "cancel_requested": False}
    updated_at = now_utc_iso()
    set_job(
        job_id,
        {
            **job,
            "cancel_requested": True,
            "status": "cancel_requested",
            "updated_at": updated_at,
        },
    )
    return {"job_id": job_id, "status": "cancel_requested", "cancel_requested": True}
