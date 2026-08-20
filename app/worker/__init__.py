import time
import traceback

from app.core.config import load_model_config
from app.models.adapter import VisionModelAdapter
from app.models.registry import get_model
from app.observability import (
    log_event,
    set_worker_health,
    set_worker_utilization,
    track_job_status,
    track_model_inference,
    track_queue_wait,
)
from app.schemas.job import JobStatus
from app.services.queue import queue_service

RETRY_BACKOFF_SECONDS = [1, 2, 4]
RECOVERY_SCAN_INTERVAL_SECONDS = 30
STALE_JOB_GRACE_SECONDS = 30
_LAST_RECOVERY_SCAN_AT = 0.0

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency fallback
    psutil = None

print("[worker] started, waiting for jobs...", flush=True)


def _now():
    return time.time()


def _job_field(job, name: str, default=None):
    if isinstance(job, dict):
        return job.get(name, default)
    return getattr(job, name, default)


def _duration_ms(job):
    started_at = _job_field(job, "started_at")
    if started_at is None:
        return None
    return int((_now() - started_at) * 1000)


def _queue_wait_ms(job):
    created_at = _job_field(job, "created_at_epoch")
    started_at = _job_field(job, "started_at")
    if created_at is None or started_at is None:
        return None
    return max(0, int((float(started_at) - float(created_at)) * 1000))


def _sample_worker_utilization():
    if psutil is None:
        return
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    gpu_percent = None
    try:
        import pynvml  # type: ignore

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_percent = float(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)
    except Exception:
        gpu_percent = None
    set_worker_utilization(cpu_percent=cpu_percent, memory_percent=memory_percent, gpu_percent=gpu_percent)


def recover_stale_jobs():
    recovered = 0
    stale_detected = 0
    now = _now()

    for job_id, job in queue_service.iter_jobs():
        if job.status != JobStatus.PROCESSING or job.started_at is None:
            continue
        deadline = float(job.started_at) + int(job.timeout_seconds) + STALE_JOB_GRACE_SECONDS
        if now <= deadline:
            continue

        stale_detected += 1
        recovered_job, retried = queue_service.recover_stale(job, duration_ms=_duration_ms(job))

        if retried:
            track_job_status("queued", job.model, job.model_version)
            log_event("job_recovered_to_queue", job_id=job_id, attempt=recovered_job.attempt)
        else:
            track_job_status("dead_lettered", job.model, job.model_version)
            log_event("job_recovered_to_dead_letter", job_id=job_id, attempt=recovered_job.attempt)
        recovered += 1

    set_worker_health(last_recovery_count=recovered, stale_jobs_detected=stale_detected)
    return recovered, stale_detected


def maybe_recover_stale_jobs():
    global _LAST_RECOVERY_SCAN_AT
    if (_now() - _LAST_RECOVERY_SCAN_AT) < RECOVERY_SCAN_INTERVAL_SECONDS:
        return
    _LAST_RECOVERY_SCAN_AT = _now()
    recover_stale_jobs()


def process_one_job():
    job_id = queue_service.dequeue()
    job = queue_service.get_job(job_id)
    active_job = job

    if job is None:
        print(f"[worker] missing job: {job_id}", flush=True)
        return

    try:
        if job.cancel_requested:
            model = job.model
            model_version = job.model_version
            queue_service.mark_cancelled(job, duration_ms=_duration_ms(job))
            track_job_status("failed", model, model_version)
            log_event("job_cancelled", job_id=job_id, model=model, model_version=model_version)
            return

        model_name = job.model
        model_version = job.model_version

        model = get_model(model_name, model_version)
        config = load_model_config(model_name)
        adapter = VisionModelAdapter(model=model, config=config)

        processing_job = queue_service.mark_processing(job, started_at=_now())
        active_job = processing_job
        queue_wait_ms = _queue_wait_ms(processing_job)
        if queue_wait_ms is not None:
            track_queue_wait(model_name, model_version or "unknown", queue_wait_ms)

        timeout_seconds = int(processing_job.timeout_seconds)
        if (_now() - float(processing_job.started_at)) > timeout_seconds:
            queue_service.mark_timed_out(processing_job, duration_ms=_duration_ms(processing_job))
            track_job_status("timed_out", model_name, model_version or "unknown")
            log_event("job_timed_out", job_id=job_id, model=model_name, model_version=model_version)
            return

        if processing_job.image_bytes_list:
            image_bytes_list = [bytes.fromhex(item) for item in processing_job.image_bytes_list]
            result = adapter.predict_batch(image_bytes_list)
        else:
            image_bytes = bytes.fromhex(processing_job.image_bytes or "")
            result = adapter.predict(image_bytes)

        if (_now() - float(processing_job.started_at)) > timeout_seconds:
            queue_service.mark_timed_out(processing_job, duration_ms=_duration_ms(processing_job))
            track_job_status("timed_out", model_name, model_version or "unknown")
            log_event("job_timed_out", job_id=job_id, model=model_name, model_version=model_version)
            return

        queue_service.persist_result(processing_job, result=result, duration_ms=_duration_ms(processing_job))
        track_job_status("completed", model_name, model_version or "unknown")
        duration_ms = _duration_ms(processing_job)
        if duration_ms is not None:
            track_model_inference(model_name, model_version or "unknown", duration_ms)
        log_event("job_completed", job_id=job_id, model=model_name, model_version=model_version)
        _sample_worker_utilization()

        print(f"[worker] completed: {job_id}", flush=True)

    except Exception as e:
        updated, retried = queue_service.handle_failure(
            active_job,
            error=e,
            duration_ms=_duration_ms(active_job),
            enqueue_retry=False,
        )

        if retried:
            backoff = RETRY_BACKOFF_SECONDS[min(updated.attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
            time.sleep(backoff)
            queue_service.requeue(updated)
            track_job_status("queued", job.model, job.model_version)
            log_event(
                "job_requeued",
                job_id=job_id,
                model=job.model,
                model_version=job.model_version,
                attempt=updated.attempt,
            )
        else:
            track_job_status("dead_lettered", job.model, job.model_version)
            log_event(
                "job_dead_lettered",
                job_id=job_id,
                model=job.model,
                model_version=job.model_version,
                attempt=updated.attempt,
            )

        print(f"[worker] failed: {job_id}", flush=True)
        traceback.print_exc()


def run_worker_forever():
    while True:
        maybe_recover_stale_jobs()
        process_one_job()
