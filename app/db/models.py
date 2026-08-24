from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc)


json_type = JSON().with_variant(JSONB, "postgresql")


class RegisteredModel(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    default_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    versions: Mapped[list["ModelVersion"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="ModelVersion.version",
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("model_id", "version", name="uq_model_versions_model_id_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    runtime: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    class_path: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[dict] = mapped_column(MutableDict.as_mutable(json_type), default=dict, nullable=False)
    output_schema: Mapped[dict] = mapped_column(MutableDict.as_mutable(json_type), default=dict, nullable=False)
    resources: Mapped[dict] = mapped_column(MutableDict.as_mutable(json_type), default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    traffic_percentage: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
    )

    deployment_strategy: Mapped[str] = mapped_column(
        String(32),
        default="stable",
        nullable=False,
    )   
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    model: Mapped[RegisteredModel] = relationship(back_populates="versions")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="model_version")


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    payload: Mapped[dict] = mapped_column(MutableDict.as_mutable(json_type), default=dict, nullable=False)
    result: Mapped[dict | list | None] = mapped_column(json_type, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    queue_latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    inference_latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    rollout_percentage: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
    )

    deployed_by: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    config: Mapped[dict] = mapped_column(MutableDict.as_mutable(json_type), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    model_version: Mapped[ModelVersion] = relationship(back_populates="deployments")


Index(
    "idx_jobs_status_created",
    JobRecord.status,
    JobRecord.created_at,
)

Index(
    "idx_jobs_model_version",
    JobRecord.model_name,
    JobRecord.model_version,
)

Index(
    "idx_model_versions_active",
    ModelVersion.model_id,
    ModelVersion.is_active,
)