from fastapi import APIRouter, HTTPException

from app.core.logging import log_event
from app.schemas.job import TERMINAL_JOB_STATUSES
from app.services import queue

router = APIRouter()


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = queue.queue_service.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail={"job_id": job_id, "reason": "Job not found"})

    response = job.public_payload()
    log_event(
        "job_status_read",
        job_id=job_id,
        status=response.get("status"),
        model=response.get("model"),
        model_version=response.get("model_version"),
    )
    return response


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    return get_status(job_id)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = queue.queue_service.request_cancel(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"job_id": job_id, "reason": "Job not found"})
    if job.status in TERMINAL_JOB_STATUSES:
        return {"job_id": job_id, "status": job.status, "cancel_requested": False}
    return {"job_id": job_id, "status": job.status, "cancel_requested": True}
