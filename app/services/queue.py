from typing import Protocol

from app.queue import redis_queue
from app.schemas.job import Job, JobStatus


class QueueBackend(Protocol):
    def enqueue_job(self, job_id: str): ...

    def enqueue_dead_letter(self, job_id: str): ...

    def dequeue_job(self): ...

    def set_job(self, job_id: str, data: dict): ...

    def get_job(self, job_id: str): ...

    def iter_jobs(self): ...

    def set_idempotency_job(self, key: str, job_id: str): ...

    def get_idempotency_job(self, key: str): ...

    def queue_depth(self) -> int: ...

    def dead_letter_depth(self) -> int: ...

    def ping(self) -> bool: ...


class RedisQueue:
    def enqueue_job(self, job_id: str):
        return redis_queue.enqueue_job(job_id)

    def enqueue_dead_letter(self, job_id: str):
        return redis_queue.enqueue_dead_letter(job_id)

    def dequeue_job(self):
        return redis_queue.dequeue_job()

    def set_job(self, job_id: str, data: dict):
        return redis_queue.set_job(job_id, data)

    def get_job(self, job_id: str):
        return redis_queue.get_job(job_id)

    def iter_jobs(self):
        return redis_queue.iter_jobs()

    def set_idempotency_job(self, key: str, job_id: str):
        return redis_queue.set_idempotency_job(key, job_id)

    def get_idempotency_job(self, key: str):
        return redis_queue.get_idempotency_job(key)

    def queue_depth(self) -> int:
        return redis_queue.queue_depth()

    def dead_letter_depth(self) -> int:
        return redis_queue.dead_letter_depth()

    def ping(self) -> bool:
        return redis_queue.ping()


class SQSQueue:
    """Placeholder adapter so SQS can implement QueueBackend without API/worker changes."""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("SQSQueue is not implemented yet")


class QueueService:
    def __init__(self, backend: QueueBackend):
        self.backend = backend

    def enqueue(self, job: Job):
        self.save_job(job)
        self.backend.enqueue_job(job.job_id)

    def requeue(self, job: Job):
        self.backend.enqueue_job(job.job_id)

    def dequeue(self) -> str:
        return self.backend.dequeue_job()

    def get_job(self, job_id: str) -> Job | None:
        payload = self.backend.get_job(job_id)
        if payload is None:
            return None
        payload = {"job_id": job_id, **payload}
        return Job.from_payload(payload)

    def save_job(self, job: Job):
        self.backend.set_job(job.job_id, job.to_payload())

    def iter_jobs(self):
        for job_id, payload in self.backend.iter_jobs():
            payload = {"job_id": job_id, **payload}
            yield job_id, Job.from_payload(payload)

    def request_cancel(self, job_id: str) -> Job | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        if job.is_terminal():
            return job
        updated = job.mark_cancel_requested()
        self.save_job(updated)
        return updated

    def mark_processing(self, job: Job, started_at: float) -> Job:
        updated = job.mark_processing(started_at)
        self.save_job(updated)
        return updated

    def persist_result(self, job: Job, result, duration_ms: int | None) -> Job:
        updated = job.mark_completed(result=result, duration_ms=duration_ms)
        self.save_job(updated)
        return updated

    def mark_timed_out(self, job: Job, duration_ms: int | None) -> Job:
        updated = job.mark_timed_out(duration_ms=duration_ms)
        self.save_job(updated)
        return updated

    def mark_cancelled(self, job: Job, duration_ms: int | None) -> Job:
        updated = job.mark_cancelled(duration_ms=duration_ms)
        self.save_job(updated)
        return updated

    def handle_failure(
        self,
        job: Job,
        error: Exception,
        duration_ms: int | None,
        enqueue_retry: bool = True,
    ) -> tuple[Job, bool]:
        failed = job.mark_failed_attempt(error=error, duration_ms=duration_ms)
        should_retry = failed.attempt <= failed.max_retries
        if should_retry:
            updated = failed.requeue_after_failure()
            self.save_job(updated)
            if enqueue_retry:
                self.requeue(updated)
            return updated, True

        updated = failed.dead_letter_after_failure()
        self.save_job(updated)
        self.backend.enqueue_dead_letter(updated.job_id)
        return updated, False

    def recover_stale(self, job: Job, duration_ms: int | None) -> tuple[Job, bool]:
        failed = job.mark_failed_attempt(
            error=RuntimeError("Recovered stale processing job after worker interruption"),
            duration_ms=duration_ms,
        ).with_updates(error_code="worker_recovery")
        should_retry = failed.attempt <= failed.max_retries
        if should_retry:
            updated = failed.requeue_after_failure().with_updates(started_at=None)
            self.save_job(updated)
            self.backend.enqueue_job(updated.job_id)
            return updated, True

        updated = failed.dead_letter_after_failure()
        self.save_job(updated)
        self.backend.enqueue_dead_letter(updated.job_id)
        return updated, False

    def set_idempotency_job(self, key: str, job_id: str):
        self.backend.set_idempotency_job(key, job_id)

    def get_idempotency_job(self, key: str):
        return self.backend.get_idempotency_job(key)

    def queue_depth(self) -> int:
        return self.backend.queue_depth()

    def dead_letter_depth(self) -> int:
        return self.backend.dead_letter_depth()

    def ping(self) -> bool:
        return self.backend.ping()


queue_service = QueueService(RedisQueue())


def enqueue_job(job_id: str):
    queue_service.backend.enqueue_job(job_id)


def enqueue_dead_letter(job_id: str):
    queue_service.backend.enqueue_dead_letter(job_id)


def dequeue_job():
    return queue_service.dequeue()


def set_job(job_id: str, data: dict):
    queue_service.backend.set_job(job_id, data)


def get_job(job_id: str):
    job = queue_service.get_job(job_id)
    return None if job is None else job.to_payload()


def iter_jobs():
    for job_id, job in queue_service.iter_jobs():
        yield job_id, job.to_payload()


def set_idempotency_job(key: str, job_id: str):
    queue_service.set_idempotency_job(key, job_id)


def get_idempotency_job(key: str):
    return queue_service.get_idempotency_job(key)


def queue_depth() -> int:
    return queue_service.queue_depth()


def dead_letter_depth() -> int:
    return queue_service.dead_letter_depth()


def ping() -> bool:
    return queue_service.ping()


__all__ = [
    "Job",
    "JobStatus",
    "QueueBackend",
    "QueueService",
    "RedisQueue",
    "SQSQueue",
    "queue_service",
]

import json
import redis

r = redis.Redis(host="redis", port=6379, decode_responses=True)

def get_all_jobs():
    jobs = []

    for key in r.scan_iter("job:*"):
        data = r.get(key)

        if data:
            jobs.append(json.loads(data))

    jobs.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True,
    )

    return jobs