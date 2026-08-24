"""model artifact checksums

Revision ID: 20260820_0002
Revises: 20260820_0001
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa

revision = "20260820_0002"
down_revision = "20260820_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("model_versions", sa.Column("artifact_sha256", sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column("model_versions", "artifact_sha256")
