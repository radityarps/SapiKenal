"""Replace breed profiles with the guide article CMS.

The downgrade is intentionally unavailable: reconstructing the split legacy fields from
article bodies would be lossy. Restore a backup if rollback past this revision is needed.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0009_article_cms"
down_revision: str | None = "0008_breed_profile_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_KEY_MAP = {
    "bali": "bali_1",
    "brahman": "brahman_1",
    "brangus": "brangus_1",
    "limusin": "limusin_1",
}
_LOCALES = {"id-ID", "en-US"}
_STATUSES = {"draft", "active", "inactive"}


def _validate_source_data(connection: sa.Connection) -> None:
    profiles = sa.table(
        "breed_profiles",
        sa.column("id"),
        sa.column("canonical_key"),
        sa.column("locale"),
        sa.column("status"),
    )
    revisions = sa.table(
        "breed_profile_revisions",
        sa.column("profile_id"),
        sa.column("revision"),
        sa.column("status"),
    )
    # Static SQLAlchemy migration expression; no caller input reaches execution.
    # pi-lens-ignore: python-sql-injection
    for row in connection.execute(sa.select(profiles)).mappings():
        if row["canonical_key"] not in _KEY_MAP:
            raise RuntimeError(
                f"Cannot migrate unsupported guide article key: {row['canonical_key']}"
            )
        if row["locale"] not in _LOCALES:
            raise RuntimeError(
                f"Cannot migrate unsupported guide article locale: {row['locale']}"
            )
        if row["status"] not in _STATUSES:
            raise RuntimeError(
                f"Cannot migrate unsupported guide article status: {row['status']}"
            )
    seen: set[tuple[str, int]] = set()
    active: set[str] = set()
    # Static SQLAlchemy migration expression; no caller input reaches execution.
    # pi-lens-ignore: python-sql-injection
    for row in connection.execute(sa.select(revisions)).mappings():
        if row["status"] not in _STATUSES:
            raise RuntimeError(
                f"Cannot migrate unsupported guide revision status: {row['status']}"
            )
        number = (row["profile_id"], row["revision"])
        if number in seen:
            raise RuntimeError("Cannot migrate duplicate guide article revision number")
        seen.add(number)
        if row["status"] == "active":
            if row["profile_id"] in active:
                raise RuntimeError(
                    "Cannot migrate multiple active revisions for one article"
                )
            active.add(row["profile_id"])


def upgrade() -> None:
    connection = op.get_bind()
    _validate_source_data(connection)

    op.rename_table("breed_profiles", "guide_articles")
    op.rename_table("breed_profile_revisions", "guide_article_revisions")
    op.drop_index("ix_breed_profiles_canonical_key", table_name="guide_articles")
    op.drop_index(
        "ix_breed_profile_revisions_profile_id",
        table_name="guide_article_revisions",
    )

    with op.batch_alter_table("guide_articles", recreate="always") as batch:
        batch.alter_column(
            "canonical_key",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            new_column_name="article_key",
        )
        batch.drop_constraint("ck_breed_profiles_canonical_key", type_="check")
        batch.drop_constraint("ck_breed_profiles_locale", type_="check")
        batch.create_check_constraint(
            "ck_guide_articles_locale", "locale IN ('id-ID', 'en-US')"
        )
        batch.create_check_constraint(
            "ck_guide_articles_status", "status IN ('draft', 'active', 'inactive')"
        )
        batch.create_unique_constraint(
            "uq_guide_articles_key_locale", ["article_key", "locale"]
        )

    guide_articles = sa.table(
        "guide_articles", sa.column("article_key", sa.String(length=64))
    )
    for old_key, article_key in _KEY_MAP.items():
        # Values come from the fixed migration mapping above.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            guide_articles.update()
            .where(guide_articles.c.article_key == old_key)
            .values(article_key=article_key)
        )

    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.alter_column(
            "profile_id",
            existing_type=sa.String(length=36),
            new_column_name="article_id",
        )
        batch.add_column(sa.Column("category", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("icon", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("sort_order", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("title", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("body", sa.Text(), nullable=True))

    articles = sa.table(
        "guide_articles",
        sa.column("id", sa.String(length=36)),
        sa.column("article_key", sa.String(length=64)),
    )
    revisions = sa.table(
        "guide_article_revisions",
        sa.column("id"),
        sa.column("article_id"),
        sa.column("display_name"),
        sa.column("strengths"),
        sa.column("limitations"),
        sa.column("disclaimer"),
        sa.column("category"),
        sa.column("icon"),
        sa.column("sort_order"),
        sa.column("title"),
        sa.column("body"),
    )
    # Static SQLAlchemy migration expressions; no caller input reaches execution.
    # pi-lens-ignore: python-sql-injection
    article_rows = {
        str(row.id): str(row.article_key)
        # pi-lens-ignore: python-sql-injection
        for row in connection.execute(sa.select(articles.c.id, articles.c.article_key))
    }
    # pi-lens-ignore: python-sql-injection
    for row in connection.execute(sa.select(revisions)).mappings():
        body = "\n\n".join(
            part
            for part in (
                f"Kelebihan\n{row['strengths']}" if row["strengths"] else "",
                f"Keterbatasan\n{row['limitations']}" if row["limitations"] else "",
                row["disclaimer"] or "",
            )
            if part
        )
        article_key = article_rows[row["article_id"]]
        # Values are derived only from validated rows in the same database.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            revisions.update()
            .where(revisions.c.id == row["id"])
            .values(
                category=article_key.removesuffix("_1"),
                icon="🐄",
                sort_order=10,
                title=row["display_name"],
                body=body or row["display_name"],
            )
        )

    with op.batch_alter_table("guide_article_revisions", recreate="always") as batch:
        batch.alter_column(
            "category", existing_type=sa.String(length=16), nullable=False
        )
        batch.alter_column("icon", existing_type=sa.String(length=16), nullable=False)
        batch.alter_column("sort_order", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("title", existing_type=sa.String(length=120), nullable=False)
        batch.alter_column("body", existing_type=sa.Text(), nullable=False)
        batch.drop_column("display_name")
        batch.drop_column("strengths")
        batch.drop_column("limitations")
        batch.drop_column("disclaimer")
        batch.drop_constraint("ck_breed_profile_revisions_status", type_="check")
        batch.create_check_constraint(
            "ck_guide_article_revisions_status",
            "status IN ('draft', 'active', 'inactive')",
        )
        batch.create_check_constraint(
            "ck_guide_article_revisions_category",
            "category IN ('app_usage', 'bali', 'brahman', 'brangus', 'limusin')",
        )
        batch.create_unique_constraint(
            "uq_guide_article_revisions_number", ["article_id", "revision"]
        )

    op.create_index("ix_guide_articles_article_key", "guide_articles", ["article_key"])
    op.create_index(
        "ix_guide_articles_locale_status", "guide_articles", ["locale", "status"]
    )
    op.create_index(
        "ix_guide_article_revisions_article_id",
        "guide_article_revisions",
        ["article_id"],
    )
    op.create_index(
        "uq_guide_article_revisions_one_active",
        "guide_article_revisions",
        ["article_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    raise RuntimeError(
        "Article CMS migration is intentionally irreversible because rebuilding legacy "
        "profile fields would lose article body structure"
    )
