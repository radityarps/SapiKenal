"""Add is_breed_profile, breed_key, and content_blocks to guide articles."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_article_breed_profile_blocks"
down_revision: str | None = "0014_remove_model_versioning"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "guide_articles",
        sa.Column(
            "is_breed_profile",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "guide_articles",
        sa.Column("breed_key", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "uq_guide_articles_breed_key",
        "guide_articles",
        ["breed_key"],
        unique=True,
        postgresql_where=sa.text("breed_key IS NOT NULL"),
        sqlite_where=sa.text("breed_key IS NOT NULL"),
    )
    op.add_column(
        "guide_article_revisions",
        sa.Column("content_blocks", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("guide_article_revisions", "content_blocks")
    op.drop_index("uq_guide_articles_breed_key", table_name="guide_articles")
    op.drop_column("guide_articles", "breed_key")
    op.drop_column("guide_articles", "is_breed_profile")
