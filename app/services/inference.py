import uuid

from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.middleware import trace_id_from_request
from app.core.logging import log_event
from app.observability import track_job_status
from app.schemas.job import Job
from app.services import queue, registry


async def enqueue_prediction(
    request,
    model: str,
    model_version: str | None,
    files: list[UploadFile],
    idempotency_key: str | None,
    batch_mode: bool,
):
    if not registry.has_model(model, model_version):
        raise HTTPException(
            status_code=400,
            detail={"model": model, "model_version": model_version, "reason": "Unknown model/version"},
        )

    if batch_mode and not files:
        raise HTTPException(status_code=400, detail={"reason": "At least one file is required"})

    for file in files:
        if file.content_type not in settings.allowed_image_mime_types:
            raise HTTPException(
                status_code=415,
                detail={"content_type": file.content_type, "allowed": sorted(settings.allowed_image_mime_types)},
            )

    resolved_version = registry.resolve_model_version(model, model_version)

    if idempotency_key:
        existing_job_id = queue.queue_service.get_idempotency_job(idempotency_key)
        if existing_job_id:
            existing = queue.queue_service.get_job(existing_job_id)
            if existing is not None:
                return {
                    "job_id": existing_job_id,
                    "model": existing.model,
                    "model_version": existing.model_version,
                    "status": existing.status,
                    "idempotency_reused": True,
                }

    image_bytes_list = [await file.read() for file in files]
    for image_bytes in image_bytes_list:
        if len(image_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail={"max_upload_bytes": settings.max_upload_bytes, "received_bytes": len(image_bytes)},
            )

    job_id = str(uuid.uuid4())
    job = Job.queued(
        job_id=job_id,
        model=model,
        model_version=resolved_version,
        timeout_seconds=settings.default_job_timeout_seconds,
        image_bytes_list=image_bytes_list,
    )

    queue.queue_service.enqueue(job)
    if idempotency_key:
        queue.queue_service.set_idempotency_job(idempotency_key, job_id)
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
