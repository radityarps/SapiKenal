"""Add dashboard, disease content, and model registry tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_admin_modules"
down_revision: str | None = "0001_admin_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "disease_contents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "locale"),
    )
    op.create_index("ix_disease_contents_slug", "disease_contents", ["slug"])
    op.create_table(
        "disease_content_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("model_class", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("handling_advice", sa.Text(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_id"], ["disease_contents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_id", "revision"),
    )
    op.create_index(
        "ix_disease_content_revisions_content_id",
        "disease_content_revisions",
        ["content_id"],
    )
    op.create_index(
        "ix_disease_content_revisions_model_class",
        "disease_content_revisions",
        ["model_class"],
    )

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
        sa.Column("registered_by", sa.String(length=36), nullable=True),
        sa.Column("activated_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["registered_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["activated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
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


def downgrade() -> None:
    op.drop_table("model_activations")
    op.drop_table("model_versions")
    op.drop_table("disease_content_revisions")
    op.drop_table("disease_contents")
