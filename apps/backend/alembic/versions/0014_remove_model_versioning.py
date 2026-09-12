"""Remove model_activations and model_versions tables."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_remove_model_versioning"
down_revision: str | None = "0013_remove_guide_article_locale"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("model_activations")
    op.drop_table("model_versions")


def downgrade() -> None:
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=128), nullable=False),
        sa.Column("artifact_name", sa.String(length=255), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("input_size", sa.Integer(), nullable=False),
        sa.Column("classes", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_by", sa.String(length=36), nullable=True),
        sa.Column("activated_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["registered_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["activated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
    )
    op.create_index(
        "uq_model_versions_one_active",
        "model_versions",
        ["status"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index("ix_model_versions_status", "model_versions", ["status"])
    op.create_table(
        "model_activations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_version_id", sa.String(length=36), nullable=False),
        sa.Column("previous_model_version_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("error_message", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["previous_model_version_id"], ["model_versions.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_model_activations_model_version_id",
        "model_activations",
        ["model_version_id"],
    )
    op.create_index(
        "ix_model_activations_created_at",
        "model_activations",
        ["created_at"],
    )
