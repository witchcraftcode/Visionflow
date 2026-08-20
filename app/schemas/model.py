from typing import Any

from pydantic import BaseModel


class RegisterModelVersionRequest(BaseModel):
    model: str
    version: str
    runtime: str
    artifact_uri: str
    class_path: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    resources: dict[str, Any]


class UpdateModelVersionRequest(BaseModel):
    runtime: str | None = None
    artifact_uri: str | None = None
    class_path: str | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    resources: dict[str, Any] | None = None


class PromoteModelVersionRequest(BaseModel):
    version: str


class AuditEventListResponse(BaseModel):
    events: list[dict[str, Any]]


class ModelRegisteredResponse(BaseModel):
    status: str
    model: str
    version: str


class ModelPromotedResponse(BaseModel):
    status: str
    model: str
    default_version: str
