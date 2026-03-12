import time
import traceback

from app.queue.redis_queue import dequeue_job, enqueue_dead_letter, enqueue_job, get_job, set_job
from app.models.adapter import VisionModelAdapter
from app.models.registry import get_model
from app.config import load_model_config
from app.observability import log_event, track_job_status

RETRY_BACKOFF_SECONDS = [1, 2, 4]

print("[worker] started, waiting for jobs...", flush=True)


def _now():
    return time.time()


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _duration_ms(job: dict):
    started_at = job.get("started_at")
    if started_at is None:
        return None
    return int((_now() - started_at) * 1000)


def process_one_job():
    job_id = dequeue_job()
    job = get_job(job_id)

    if job is None:
        print(f"[worker] missing job: {job_id}", flush=True)
        return

    try:
        if job.get("cancel_requested"):
            model = job.get("model", "unknown")
            model_version = job.get("model_version", "unknown")
            set_job(
                job_id,
                {
                    **job,
                    "status": "failed",
                    "error_code": "cancelled",
                    "error": "Job cancelled before processing",
                    "updated_at": _now_iso(),
                    "duration_ms": _duration_ms(job),
                },
            )
            track_job_status("failed", model, model_version)
            log_event("job_cancelled", job_id=job_id, model=model, model_version=model_version)
            return

        model_name = job["model"]
        model_version = job.get("model_version")

        model = get_model(model_name, model_version)
        config = load_model_config(model_name)
        adapter = VisionModelAdapter(model=model, config=config)

        processing_job = {
            **job,
            "status": "processing",
            "error_code": None,
            "error": None,
            "started_at": job.get("started_at", _now()),
            "updated_at": _now_iso(),
        }
        set_job(job_id, processing_job)

        timeout_seconds = int(processing_job.get("timeout_seconds", 60))
        if (_now() - float(processing_job["started_at"])) > timeout_seconds:
            timed_out = {
                **processing_job,
                "status": "timed_out",
                "error_code": "timeout",
                "error": f"Processing exceeded timeout ({timeout_seconds}s)",
                "updated_at": _now_iso(),
                "duration_ms": _duration_ms(processing_job),
            }
            set_job(job_id, timed_out)
            track_job_status("timed_out", model_name, model_version or "unknown")
            log_event("job_timed_out", job_id=job_id, model=model_name, model_version=model_version)
            return

        image_bytes = bytes.fromhex(processing_job["image_bytes"])
        result = adapter.predict(image_bytes)

        if (_now() - float(processing_job["started_at"])) > timeout_seconds:
            timed_out = {
                **processing_job,
                "status": "timed_out",
                "error_code": "timeout",
                "error": f"Processing exceeded timeout ({timeout_seconds}s)",
                "updated_at": _now_iso(),
                "duration_ms": _duration_ms(processing_job),
            }
            set_job(job_id, timed_out)
            track_job_status("timed_out", model_name, model_version or "unknown")
            log_event("job_timed_out", job_id=job_id, model=model_name, model_version=model_version)
            return

        set_job(job_id, {
            **processing_job,
            "status": "completed",
            "result": result,
            "error_code": None,
            "error": None,
            "updated_at": _now_iso(),
            "duration_ms": _duration_ms(processing_job),
        })
        track_job_status("completed", model_name, model_version or "unknown")
        log_event("job_completed", job_id=job_id, model=model_name, model_version=model_version)

        print(f"[worker] completed: {job_id}", flush=True)

    except Exception as e:
        attempt = int(job.get("attempt", 0)) + 1
        max_retries = int(job.get("max_retries", 3))

        failed = {
            **job,
            "attempt": attempt,
            "status": "failed",
            "result": None,
            "error_code": "runtime_error",
            "error": str(e),
            "updated_at": _now_iso(),
            "duration_ms": _duration_ms(job),
        }

        if attempt <= max_retries:
            backoff = RETRY_BACKOFF_SECONDS[min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
            set_job(job_id, {**failed, "status": "queued"})
            time.sleep(backoff)
            enqueue_job(job_id)
            track_job_status("queued", job.get("model", "unknown"), job.get("model_version", "unknown"))
            log_event(
                "job_requeued",
                job_id=job_id,
                model=job.get("model"),
                model_version=job.get("model_version"),
                attempt=attempt,
            )
        else:
            dead_lettered = {**failed, "status": "dead_lettered"}
            set_job(job_id, dead_lettered)
            enqueue_dead_letter(job_id)
            track_job_status("dead_lettered", job.get("model", "unknown"), job.get("model_version", "unknown"))
            log_event(
                "job_dead_lettered",
                job_id=job_id,
                model=job.get("model"),
                model_version=job.get("model_version"),
                attempt=attempt,
            )

        print(f"[worker] failed: {job_id}", flush=True)
        traceback.print_exc()


def run_worker_forever():
    while True:
        process_one_job()
