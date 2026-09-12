"""Remove locale column and constraints from guide_articles."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0013_remove_guide_article_locale"
down_revision: str | None = "0012_remove_location_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    # Delete revisions belonging to non-id-ID articles
    connection.execute(
        sa.text(
            "DELETE FROM guide_article_revisions WHERE article_id IN ("
            "  SELECT id FROM guide_articles WHERE locale != 'id-ID'"
            ")"
        )
    )
    # Delete non-id-ID articles
    connection.execute(sa.text("DELETE FROM guide_articles WHERE locale != 'id-ID'"))

    with op.batch_alter_table("guide_articles", recreate="always") as batch:
        batch.drop_constraint("ck_guide_articles_locale", type_="check")
        batch.drop_index("ix_guide_articles_locale_status")
        batch.drop_column("locale")
        if connection.dialect.name == "postgresql":
            batch.drop_constraint("uq_guide_articles_key_locale", type_="unique")
        batch.create_unique_constraint(
            "uq_guide_articles_article_key", ["article_key"]
        )

    op.create_index("ix_guide_articles_status", "guide_articles", ["status"])


def downgrade() -> None:
    connection = op.get_bind()
    op.drop_index("ix_guide_articles_status", table_name="guide_articles")

    with op.batch_alter_table("guide_articles", recreate="always") as batch:
        if connection.dialect.name == "postgresql":
            batch.drop_constraint("uq_guide_articles_article_key", type_="unique")
        batch.add_column(
            sa.Column(
                "locale",
                sa.String(length=16),
                nullable=False,
                server_default="id-ID",
            )
        )
        batch.create_check_constraint(
            "ck_guide_articles_locale", "locale IN ('id-ID', 'en-US')"
        )
        batch.create_unique_constraint(
            "uq_guide_articles_key_locale", ["article_key", "locale"]
        )
        batch.create_index(
            "ix_guide_articles_locale_status", ["locale", "status"]
        )
