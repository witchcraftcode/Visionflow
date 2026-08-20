"""registry postgres schema

Revision ID: 20260820_0001
Revises:
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260820_0001"
down_revision = None
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade():
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("default_version", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_models_name", "models", ["name"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("runtime", sa.String(length=64), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("class_path", sa.Text(), nullable=False),
        sa.Column("input_schema", _json_type(), nullable=False),
        sa.Column("output_schema", _json_type(), nullable=False),
        sa.Column("resources", _json_type(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("model_id", "version", name="uq_model_versions_model_id_version"),
    )
    op.create_index("ix_model_versions_model_id", "model_versions", ["model_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("payload", _json_type(), nullable=False),
        sa.Column("result", _json_type(), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_jobs_job_id", "jobs", ["job_id"])
    op.create_index("ix_jobs_model_name", "jobs", ["model_name"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("model_version_id", sa.Integer(), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("environment", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("config", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_deployments_name", "deployments", ["name"])
    op.create_index("ix_deployments_model_version_id", "deployments", ["model_version_id"])


def downgrade():
    op.drop_index("ix_deployments_model_version_id", table_name="deployments")
    op.drop_index("ix_deployments_name", table_name="deployments")
    op.drop_table("deployments")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_model_name", table_name="jobs")
    op.drop_index("ix_jobs_job_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_model_versions_model_id", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_models_name", table_name="models")
    op.drop_table("models")
