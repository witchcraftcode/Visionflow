from fastapi import APIRouter, HTTPException, Request

from app.audit import list_admin_audit_events, record_admin_audit_event
from app.core.logging import log_event
from app.core.middleware import trace_id_from_request
from app.schemas.model import (
    AuditEventListResponse,
    PromoteModelVersionRequest,
    RegisterModelVersionRequest,
    UpdateModelVersionRequest,
)
from app.services import registry

router = APIRouter()


@router.get("/models")
def available_models():
    models = registry.list_models()
    return {
        "available_models": models,
        "models": [
            {
                "name": model,
                "default_version": registry.model_metadata(model)["default_version"],
                "versions": registry.list_model_versions(model),
            }
            for model in models
        ],
    }


@router.get("/models/{model_name}/versions")
def model_versions(model_name: str):
    if not registry.has_model(model_name):
        raise HTTPException(status_code=404, detail={"model": model_name, "reason": "Unknown model"})
    return {
        "model": model_name,
        "default_version": registry.model_metadata(model_name)["default_version"],
        "versions": [
            registry.model_metadata(model_name, version)
            for version in registry.list_model_versions(model_name)
        ],
    }


@router.get("/models/{model_name}/versions/{version}")
def model_version(model_name: str, version: str):
    try:
        return registry.model_metadata(model_name, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"reason": str(exc)})


@router.post("/models/register")
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
        registry.register_model_version(payload.model, payload.version, registry_payload)
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


@router.put("/models/{model_name}/versions/{version}")
def update_model_version(
    model_name: str,
    version: str,
    request: Request,
    payload: UpdateModelVersionRequest,
):
    if payload.runtime is not None and payload.runtime != "onnx":
        raise HTTPException(
            status_code=400,
            detail={"runtime": payload.runtime, "reason": "Only 'onnx' runtime is currently supported"},
        )
    if payload.class_path is not None and "." not in payload.class_path:
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
        registry.update_model_version(model_name, version, registry_payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"reason": str(exc)})
    record_admin_audit_event(
        "model_version_updated",
        trace_id=trace_id_from_request(request),
        model=model_name,
        version=version,
    )
    log_event("model_version_updated", model=model_name, version=version)
    return {"status": "updated", "model": model_name, "version": version}


@router.delete("/models/{model_name}/versions/{version}")
def delete_model_version(model_name: str, version: str, request: Request):
    try:
        registry.delete_model_version(model_name, version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"reason": str(exc)})
    record_admin_audit_event(
        "model_version_deleted",
        trace_id=trace_id_from_request(request),
        model=model_name,
        version=version,
    )
    log_event("model_version_deleted", model=model_name, version=version)
    return {"status": "deleted", "model": model_name, "version": version}


@router.post("/models/{model_name}/promote")
def promote_model(model_name: str, request: Request, payload: PromoteModelVersionRequest):
    try:
        registry.promote_model_version(model_name, payload.version)
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


@router.get("/admin/audit", response_model=AuditEventListResponse)
def admin_audit(limit: int = 50):
    return {"events": list_admin_audit_events(limit=limit)}
