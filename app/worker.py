from app.queue.redis_queue import dequeue_job, get_job, set_job
from app.models.adapter import VisionModelAdapter
from app.models.registry import get_model
from app.config import load_model_config
import traceback

print("[worker] started, waiting for jobs...", flush=True)


def process_one_job():
    job_id = dequeue_job()
    job = get_job(job_id)

    if job is None:
        print(f"[worker] missing job: {job_id}", flush=True)
        return

    try:
        model_name = job["model"]

        model = get_model(model_name)
        config = load_model_config(model_name)
        adapter = VisionModelAdapter(model=model, config=config)

        set_job(job_id, {**job, "status": "processing", "error": None})

        image_bytes = bytes.fromhex(job["image_bytes"])
        result = adapter.predict(image_bytes)

        set_job(job_id, {
            **job,
            "status": "completed",
            "result": result,
            "error": None
        })

        print(f"[worker] completed: {job_id}", flush=True)

    except Exception as e:
        set_job(job_id, {
            **job,
            "status": "failed",
            "result": None,
            "error": str(e)
        })
        print(f"[worker] failed: {job_id}", flush=True)
        traceback.print_exc()


def run_worker_forever():
    while True:
        process_one_job()
