"""Remove content_reviewed column from guide article revisions."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_remove_article_content_reviewed"
down_revision: str | None = "0015_article_breed_profile_blocks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.drop_column("content_reviewed")


def downgrade() -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.add_column(
            sa.Column(
                "content_reviewed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
