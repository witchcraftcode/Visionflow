from pydantic import BaseModel


class PredictResponse(BaseModel):
    job_id: str
    model: str
    model_version: str
    batch_count: int | None = None
    status: str
    idempotency_reused: bool
