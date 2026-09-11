"""Add mobile sync metadata to breed-identification history."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0007_history_sync_metadata"
down_revision: str | None = "0006_four_class_prediction_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    sa.Column("title", sa.String(length=120), nullable=True),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("consent_status", sa.String(length=32), nullable=True),
    sa.Column("image_source", sa.String(length=32), nullable=True),
    sa.Column("preprocessing_summary", sa.String(length=500), nullable=True),
    sa.Column("latitude", sa.Float(), nullable=True),
    sa.Column("longitude", sa.Float(), nullable=True),
    sa.Column("location_source", sa.String(length=32), nullable=True),
)


def upgrade() -> None:
    for column in _COLUMNS:
        op.add_column("detection_history", column)


def downgrade() -> None:
    for column in reversed(_COLUMNS):
        op.drop_column("detection_history", column.name)
