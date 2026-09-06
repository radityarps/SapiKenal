"""Add canonical keys and review metadata to breed profiles."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0008_breed_profile_review"
down_revision: str | None = "0007_history_sync_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CANONICAL_KEYS = {"bali", "brahman", "brangus", "limusin"}


def upgrade() -> None:
    connection = op.get_bind()
    # Static SQLAlchemy expression; no caller input reaches this migration.
    # pi-lens-ignore: python-sql-injection
    rows = connection.execute(
        sa.select(sa.column("slug"), sa.column("locale")).select_from(
            sa.table("breed_profiles")
        )
    ).mappings()
    invalid = next(
        (
            row
            for row in rows
            if row["slug"] not in _CANONICAL_KEYS
            or row["locale"] not in {"id-ID", "en-US"}
        ),
        None,
    )
    if invalid is not None:
        raise RuntimeError(
            "Existing breed profile keys must already use the canonical contract; "
            f"unsupported key/locale: {invalid['slug']}/{invalid['locale']}"
        )

    op.drop_index("ix_breed_profiles_slug", table_name="breed_profiles")
    with op.batch_alter_table("breed_profiles", recreate="always") as batch_op:
        batch_op.alter_column(
            "slug",
            existing_type=sa.String(length=80),
            type_=sa.String(length=32),
            new_column_name="canonical_key",
        )
    op.create_index(
        "ix_breed_profiles_canonical_key",
        "breed_profiles",
        ["canonical_key"],
    )

    op.drop_index(
        "ix_breed_profile_revisions_model_class",
        table_name="breed_profile_revisions",
    )
    with op.batch_alter_table("breed_profile_revisions", recreate="always") as batch_op:
        batch_op.drop_column("model_class")
    op.add_column(
        "breed_profile_revisions",
        sa.Column(
            "sources",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.add_column(
        "breed_profile_revisions",
        sa.Column(
            "content_reviewed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    with op.batch_alter_table("breed_profiles", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "ck_breed_profiles_canonical_key",
            "canonical_key IN ('bali', 'brahman', 'brangus', 'limusin')",
        )
        batch_op.create_check_constraint(
            "ck_breed_profiles_locale",
            "locale IN ('id-ID', 'en-US')",
        )
    with op.batch_alter_table("breed_profile_revisions", recreate="always") as batch_op:
        batch_op.create_check_constraint(
            "ck_breed_profile_revisions_status",
            "status IN ('draft', 'active', 'inactive')",
        )
    # Existing content has no recorded review or sources. Keep it out of public
    # delivery until an administrator explicitly reviews and activates it.
    breed_profiles = sa.table(
        "breed_profiles",
        sa.column("status", sa.String(length=16)),
    )
    breed_profile_revisions = sa.table(
        "breed_profile_revisions",
        sa.column("status", sa.String(length=16)),
    )
    op.execute(
        breed_profiles.update()
        .where(breed_profiles.c.status == "active")
        .values(status="draft")
    )
    op.execute(
        breed_profile_revisions.update()
        .where(breed_profile_revisions.c.status == "active")
        .values(status="draft")
    )


def downgrade() -> None:
    with op.batch_alter_table("breed_profile_revisions", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_breed_profile_revisions_status", type_="check")
    with op.batch_alter_table("breed_profiles", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_breed_profiles_locale", type_="check")
        batch_op.drop_constraint("ck_breed_profiles_canonical_key", type_="check")
    with op.batch_alter_table("breed_profile_revisions", recreate="always") as batch_op:
        batch_op.drop_column("content_reviewed")
        batch_op.drop_column("sources")
    with op.batch_alter_table("breed_profile_revisions", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("model_class", sa.String(length=32), nullable=True)
        )
    op.create_index(
        "ix_breed_profile_revisions_model_class",
        "breed_profile_revisions",
        ["model_class"],
    )
    op.drop_index("ix_breed_profiles_canonical_key", table_name="breed_profiles")
    with op.batch_alter_table("breed_profiles", recreate="always") as batch_op:
        batch_op.alter_column(
            "canonical_key",
            existing_type=sa.String(length=32),
            type_=sa.String(length=80),
            new_column_name="slug",
        )
    op.create_index("ix_breed_profiles_slug", "breed_profiles", ["slug"])
