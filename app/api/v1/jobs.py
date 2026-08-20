from fastapi import APIRouter, HTTPException

from app.core.logging import log_event
from app.services import queue
from app.services.inference import now_utc_iso

router = APIRouter()


@router.get("/status/{job_id}")
def get_status(job_id: str):
    job = queue.get_job(job_id)

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


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    return get_status(job_id)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"job_id": job_id, "reason": "Job not found"})
    if job["status"] in {"completed", "failed", "timed_out", "dead_lettered"}:
        return {"job_id": job_id, "status": job["status"], "cancel_requested": False}
    updated_at = now_utc_iso()
    queue.set_job(
        job_id,
        {
            **job,
            "cancel_requested": True,
            "status": "cancel_requested",
            "updated_at": updated_at,
        },
    )
    return {"job_id": job_id, "status": "cancel_requested", "cancel_requested": True}
