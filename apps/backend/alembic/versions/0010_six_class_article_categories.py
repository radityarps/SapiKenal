"""Allow guide article categories for the six-class model contract."""

from __future__ import annotations

from collections.abc import Sequence

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0010_six_class_article_categories"
down_revision: str | None = "0009_article_cms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_CATEGORIES = "'app_usage', 'aceh', 'bali', 'brahman', 'brangus', 'limusin', 'madura', 'pasundan', 'po'"
_OLD_CATEGORIES = "'app_usage', 'bali', 'brahman', 'brangus', 'limusin'"


def _replace_category_constraint(categories: str) -> None:
    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.drop_constraint("ck_guide_article_revisions_category", type_="check")
        batch.create_check_constraint(
            "ck_guide_article_revisions_category",
            f"category IN ({categories})",
        )


def upgrade() -> None:
    _replace_category_constraint(_NEW_CATEGORIES)


def downgrade() -> None:
    _replace_category_constraint(_OLD_CATEGORIES)
