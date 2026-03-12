import uuid
from datetime import datetime, timezone

from app.queue.redis_queue import enqueue_job, set_job, get_job
from app.worker import process_one_job


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


with open("test.jpg", "rb") as f:
    image_bytes = f.read()

job_id = str(uuid.uuid4())
created_at = now_utc_iso()

set_job(job_id, {
    "job_id": job_id,
    "status": "queued",
    "model": "resnet18",
    "model_version": "1.0.0",
    "created_at": created_at,
    "updated_at": created_at,
    "duration_ms": None,
    "attempt": 0,
    "max_retries": 3,
    "timeout_seconds": 60,
    "cancel_requested": False,
    "error_code": None,
    "image_bytes": image_bytes.hex(),
    "result": None,
    "error": None
})

enqueue_job(job_id)

process_one_job()

print("FINAL JOB STATE:")
print(get_job(job_id))
