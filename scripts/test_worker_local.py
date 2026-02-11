import uuid
from app.queue.redis_queue import enqueue_job, set_job, get_job
from app.worker import process_one_job
from app.config import models

with open("test.jpg", "rb") as f:
    image_bytes = f.read()

job_id = str(uuid.uuid4())

set_job(job_id, {
    "status": "queued",
    "model": "resnet18",
    "image_bytes": image_bytes.hex(),
    "result": None,
    "error": None
})

enqueue_job(job_id)

process_one_job()

print("FINAL JOB STATE:")
print(get_job(job_id))
