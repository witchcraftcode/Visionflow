from typing import Any

from pydantic import BaseModel


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
