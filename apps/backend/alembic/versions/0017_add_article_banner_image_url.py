"""Add banner_image_url to guide article revisions."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_add_article_banner_image_url"
down_revision: str | None = "0016_remove_article_content_reviewed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.add_column(
            sa.Column("banner_image_url", sa.String(512), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.drop_column("banner_image_url")
