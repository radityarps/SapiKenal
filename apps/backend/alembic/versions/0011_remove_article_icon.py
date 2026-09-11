"""Remove icon column from guide article revisions."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0011_remove_article_icon"
down_revision: str | None = "0010_six_class_article_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.drop_column("icon")


def downgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.add_column(
            sa.Column("icon", sa.String(length=16), nullable=False, server_default="📄")
        )
