from pydantic import BaseModel


class DriftBaselineRequest(BaseModel):
    baseline: dict[str, dict[str, float]]


class DriftObserveRequest(BaseModel):
    features: dict[str, float]
    label: str | None = None
