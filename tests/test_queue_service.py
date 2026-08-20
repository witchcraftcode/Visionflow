from app.schemas.job import Job, JobStatus
from app.services.queue import QueueService


class InMemoryQueueBackend:
    def __init__(self):
        self.store = {}
        self.enqueued = []
        self.dead_lettered = []
        self.idempotency = {}

    def enqueue_job(self, job_id: str):
        self.enqueued.append(job_id)

    def enqueue_dead_letter(self, job_id: str):
        self.dead_lettered.append(job_id)

    def dequeue_job(self):
        return self.enqueued.pop(0)

    def set_job(self, job_id: str, data: dict):
        self.store[job_id] = data

    def get_job(self, job_id: str):
        return self.store.get(job_id)

    def iter_jobs(self):
        return iter(self.store.items())

    def set_idempotency_job(self, key: str, job_id: str):
        self.idempotency[key] = job_id

    def get_idempotency_job(self, key: str):
        return self.idempotency.get(key)

    def queue_depth(self) -> int:
        return len(self.enqueued)

    def dead_letter_depth(self) -> int:
        return len(self.dead_lettered)

    def ping(self) -> bool:
        return True


def queued_job(job_id="job-1", attempt=0, max_retries=3):
    job = Job.queued(
        job_id=job_id,
        model="resnet18",
        model_version="1.0.0",
        timeout_seconds=60,
        image_bytes_list=[b"image"],
    )
    return job.with_updates(attempt=attempt, max_retries=max_retries)


def test_queue_service_persists_result_without_image_bytes_in_public_payload():
    backend = InMemoryQueueBackend()
    service = QueueService(backend)
    service.enqueue(queued_job())

    job = service.get_job("job-1")
    completed = service.persist_result(job, result={"label": 1}, duration_ms=42)

    assert completed.status == JobStatus.COMPLETED
    assert backend.store["job-1"]["result"] == {"label": 1}
    assert "image_bytes" not in completed.public_payload()


def test_queue_service_retries_failed_job():
    backend = InMemoryQueueBackend()
    service = QueueService(backend)
    job = queued_job()
    service.save_job(job)

    updated, retried = service.handle_failure(job, RuntimeError("temporary"), duration_ms=7)

    assert retried is True
    assert updated.status == JobStatus.QUEUED
    assert updated.attempt == 1
    assert backend.enqueued == ["job-1"]


def test_queue_service_dead_letters_exhausted_job():
    backend = InMemoryQueueBackend()
    service = QueueService(backend)
    job = queued_job(attempt=3, max_retries=3)
    service.save_job(job)

    updated, retried = service.handle_failure(job, RuntimeError("permanent"), duration_ms=7)

    assert retried is False
    assert updated.status == JobStatus.DEAD_LETTERED
    assert backend.dead_lettered == ["job-1"]


def test_queue_service_requests_cancel_for_non_terminal_job():
    backend = InMemoryQueueBackend()
    service = QueueService(backend)
    service.save_job(queued_job())

    cancelled = service.request_cancel("job-1")

    assert cancelled.status == JobStatus.CANCEL_REQUESTED
    assert cancelled.cancel_requested is True
