"""Add model-version lifecycle timestamps."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_model_lifecycle_timestamps"
down_revision: str | None = "0003_model_active_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_versions",
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "model_versions",
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("model_versions", "rolled_back_at")
    op.drop_column("model_versions", "deactivated_at")
