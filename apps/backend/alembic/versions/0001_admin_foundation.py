"""Create the fresh admin foundation database schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_admin_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_status", "users", ["status"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False
    )
    op.create_index(
        "ix_auth_sessions_revoked_at", "auth_sessions", ["revoked_at"], unique=False
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("changed_fields", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index(
        "ix_audit_logs_request_id", "audit_logs", ["request_id"], unique=False
    )
    op.create_index(
        "ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False
    )
    op.create_index(
        "ix_audit_logs_actor_action",
        "audit_logs",
        ["actor_user_id", "action"],
        unique=False,
    )

    op.create_table(
        "detection_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("local_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.Integer(), nullable=False),
        sa.Column("predicted_class", sa.String(length=32), nullable=False),
        sa.Column("display_label", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("inference_mode", sa.String(length=32), nullable=False),
        sa.Column("is_reliable", sa.Boolean(), nullable=False),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column("app_version", sa.String(length=64), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "device_id", "local_id", name="uq_detection_history_device_local"
        ),
    )
    op.create_index(
        "ix_detection_history_device_id",
        "detection_history",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        "ix_detection_history_user_id", "detection_history", ["user_id"], unique=False
    )
    op.create_index(
        "ix_detection_history_timestamp",
        "detection_history",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_detection_history_predicted_class",
        "detection_history",
        ["predicted_class"],
        unique=False,
    )
    op.create_index(
        "ix_detection_history_confidence",
        "detection_history",
        ["confidence"],
        unique=False,
    )

    op.create_table(
        "prediction_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("history_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["history_id"], ["detection_history.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prediction_events_history_id",
        "prediction_events",
        ["history_id"],
        unique=False,
    )
    op.create_index(
        "ix_prediction_events_user_id", "prediction_events", ["user_id"], unique=False
    )
    op.create_index(
        "ix_prediction_events_request_id",
        "prediction_events",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_prediction_events_status", "prediction_events", ["status"], unique=False
    )
    op.create_index(
        "ix_prediction_events_created_at",
        "prediction_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("prediction_events")
    op.drop_table("detection_history")
    op.drop_table("audit_logs")
    op.drop_table("auth_sessions")
    op.drop_table("users")
