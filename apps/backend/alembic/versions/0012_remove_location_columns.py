"""Remove location columns from detection history."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0012_remove_location_columns"
down_revision: str | None = "0011_remove_article_icon"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("detection_history", recreate="always") as batch:
        batch.drop_column("latitude")
        batch.drop_column("longitude")
        batch.drop_column("location_source")


def downgrade() -> None:
    with op.batch_alter_table("detection_history", recreate="always") as batch:
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("location_source", sa.String(length=32), nullable=True))
