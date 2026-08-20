from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    DEAD_LETTERED = "dead_lettered"
    CANCEL_REQUESTED = "cancel_requested"


TERMINAL_JOB_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.TIMED_OUT,
    JobStatus.DEAD_LETTERED,
}


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def now_utc_epoch():
    return datetime.now(timezone.utc).timestamp()


class Job(BaseModel):
    job_id: str
    status: JobStatus
    model: str
    model_version: str = "unknown"
    created_at: str = Field(default_factory=now_utc_iso)
    created_at_epoch: float = Field(default_factory=now_utc_epoch)
    updated_at: str = Field(default_factory=now_utc_iso)
    duration_ms: int | None = None
    attempt: int = 0
    max_retries: int = 3
    timeout_seconds: int = 60
    cancel_requested: bool = False
    error_code: str | None = None
    batch_count: int = 1
    batch_total_bytes: int = 0
    result: Any = None
    error: Any = None
    started_at: float | None = None
    image_bytes: str | None = None
    image_bytes_list: list[str] | None = None

    @classmethod
    def queued(
        cls,
        job_id: str,
        model: str,
        model_version: str,
        timeout_seconds: int,
        image_bytes_list: list[bytes],
    ):
        created_at = now_utc_iso()
        payload = {
            "job_id": job_id,
            "status": JobStatus.QUEUED,
            "model": model,
            "model_version": model_version,
            "created_at": created_at,
            "created_at_epoch": now_utc_epoch(),
            "updated_at": created_at,
            "timeout_seconds": timeout_seconds,
            "batch_count": len(image_bytes_list),
            "batch_total_bytes": sum(len(image_bytes) for image_bytes in image_bytes_list),
        }
        if len(image_bytes_list) > 1:
            payload["image_bytes_list"] = [image_bytes.hex() for image_bytes in image_bytes_list]
        else:
            payload["image_bytes"] = image_bytes_list[0].hex()
        return cls(**payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]):
        return cls(**payload)

    def to_payload(self) -> dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump(mode="json")
        return self.dict()

    def public_payload(self) -> dict[str, Any]:
        payload = self.to_payload()
        payload.pop("image_bytes", None)
        payload.pop("image_bytes_list", None)
        return payload

    def is_terminal(self) -> bool:
        return self.status in TERMINAL_JOB_STATUSES

    def with_updates(self, **updates):
        if hasattr(self, "model_copy"):
            return self.model_copy(update=updates)
        return self.copy(update=updates)

    def mark_cancel_requested(self):
        return self.with_updates(
            cancel_requested=True,
            status=JobStatus.CANCEL_REQUESTED,
            updated_at=now_utc_iso(),
        )

    def mark_processing(self, started_at: float):
        return self.with_updates(
            status=JobStatus.PROCESSING,
            error_code=None,
            error=None,
            started_at=started_at,
            updated_at=now_utc_iso(),
        )

    def mark_completed(self, result: Any, duration_ms: int | None):
        return self.with_updates(
            status=JobStatus.COMPLETED,
            result=result,
            error_code=None,
            error=None,
            updated_at=now_utc_iso(),
            duration_ms=duration_ms,
        )

    def mark_timed_out(self, duration_ms: int | None):
        return self.with_updates(
            status=JobStatus.TIMED_OUT,
            error_code="timeout",
            error=f"Processing exceeded timeout ({self.timeout_seconds}s)",
            updated_at=now_utc_iso(),
            duration_ms=duration_ms,
        )

    def mark_cancelled(self, duration_ms: int | None):
        return self.with_updates(
            status=JobStatus.FAILED,
            error_code="cancelled",
            error="Job cancelled before processing",
            updated_at=now_utc_iso(),
            duration_ms=duration_ms,
        )

    def mark_failed_attempt(self, error: Exception, duration_ms: int | None):
        return self.with_updates(
            attempt=int(self.attempt) + 1,
            status=JobStatus.FAILED,
            result=None,
            error_code="runtime_error",
            error=str(error),
            updated_at=now_utc_iso(),
            duration_ms=duration_ms,
        )

    def requeue_after_failure(self):
        return self.with_updates(status=JobStatus.QUEUED)

    def dead_letter_after_failure(self):
        return self.with_updates(status=JobStatus.DEAD_LETTERED)


class JobQueuedResponse(BaseModel):
    job_id: str
    model: str
    model_version: str
    batch_count: int | None = None
    status: str
    idempotency_reused: bool


class JobCancelResponse(BaseModel):
    job_id: str
    status: str
    cancel_requested: bool


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    model: str | None = None
    model_version: str | None = None
    result: Any = None
    error: Any = None
