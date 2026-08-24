"""add production mlops metadata

Revision ID: 20260824_0622
Revises: 20260820_0002
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0622"
down_revision: Union[str, Sequence[str], None] = "20260820_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------- model_versions ----------------
    op.add_column(
        "model_versions",
        sa.Column(
            "traffic_percentage",
            sa.Float(),
            nullable=False,
            server_default="100",
        ),
    )

    op.add_column(
        "model_versions",
        sa.Column(
            "deployment_strategy",
            sa.String(length=32),
            nullable=False,
            server_default="stable",
        ),
    )

    # ---------------- jobs ----------------
    op.add_column(
        "jobs",
        sa.Column("queue_latency_ms", sa.Integer(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("inference_latency_ms", sa.Integer(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("total_latency_ms", sa.Integer(), nullable=True),
    )

    # ---------------- deployments ----------------
    op.add_column(
        "deployments",
        sa.Column(
            "rollout_percentage",
            sa.Float(),
            nullable=False,
            server_default="100",
        ),
    )

    op.add_column(
        "deployments",
        sa.Column("deployed_by", sa.String(length=128), nullable=True),
    )

    # ---------------- indexes ----------------
    op.create_index(
        "idx_jobs_model_version",
        "jobs",
        ["model_name", "model_version"],
        unique=False,
    )

    op.create_index(
        "idx_jobs_status_created",
        "jobs",
        ["status", "created_at"],
        unique=False,
    )

    op.create_index(
        "idx_model_versions_active",
        "model_versions",
        ["model_id", "is_active"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("idx_model_versions_active", table_name="model_versions")
    op.drop_index("idx_jobs_status_created", table_name="jobs")
    op.drop_index("idx_jobs_model_version", table_name="jobs")

    op.drop_column("deployments", "deployed_by")
    op.drop_column("deployments", "rollout_percentage")

    op.drop_column("jobs", "total_latency_ms")
    op.drop_column("jobs", "inference_latency_ms")
    op.drop_column("jobs", "queue_latency_ms")

    op.drop_column("model_versions", "deployment_strategy")
    op.drop_column("model_versions", "traffic_percentage")