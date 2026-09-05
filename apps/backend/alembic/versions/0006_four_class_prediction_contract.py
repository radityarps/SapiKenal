"""Replace legacy prediction and disease-content tables with breed schemas."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

# pi-lens-ignore: python-hallucinated-import
from alembic import op  # type: ignore[reportAttributeAccessIssue]

revision: str = "0006_four_class_prediction_contract"
down_revision: str | None = "0005_four_class_prediction_contract"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HISTORY_COLUMNS = {
    "id",
    "device_id",
    "local_id",
    "user_id",
    "timestamp",
    "predicted_class",
    "display_label",
    "confidence",
    "scores",
    "inference_mode",
    "is_reliable",
    "processing_ms",
    "app_version",
    "model_version",
    "created_at",
    "updated_at",
}
_EVENT_COLUMNS = {
    "id",
    "history_id",
    "user_id",
    "request_id",
    "status",
    "error_code",
    "predicted_class",
    "confidence",
    "scores",
    "processing_ms",
    "model_version",
    "created_at",
}
_PROFILE_COLUMNS = {
    "id",
    "slug",
    "locale",
    "status",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
}
_REVISION_COLUMNS = {
    "id",
    "profile_id",
    "revision",
    "model_class",
    "display_name",
    "summary",
    "strengths",
    "limitations",
    "disclaimer",
    "status",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
}
_ROW_CHECKS = {
    "detection_history": "SELECT 1 FROM detection_history LIMIT 1",
    "prediction_events": "SELECT 1 FROM prediction_events LIMIT 1",
    "disease_contents": "SELECT 1 FROM disease_contents LIMIT 1",
    "disease_content_revisions": "SELECT 1 FROM disease_content_revisions LIMIT 1",
    "breed_profiles": "SELECT 1 FROM breed_profiles LIMIT 1",
    "breed_profile_revisions": "SELECT 1 FROM breed_profile_revisions LIMIT 1",
}


def _table_exists(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def _table_columns(table: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table)}


def _table_has_rows(table: str) -> bool:
    # Queries are selected from the fixed allowlist above; no caller input reaches SQL.
    # pi-lens-ignore: python-sql-injection
    return op.get_bind().execute(sa.text(_ROW_CHECKS[table])).first() is not None


def _drop_if_exists(table: str) -> None:
    if _table_exists(table):
        op.drop_table(table)


def _needs_replacement(table: str, expected_columns: set[str]) -> bool:
    return not _table_exists(table) or _table_columns(table) != expected_columns


def _assert_safe_reset(table: str) -> None:
    if _table_exists(table) and _table_has_rows(table):
        raise RuntimeError(
            f"{table} contains legacy data that cannot be mapped to the breed schema; "
            "back it up and reset it explicitly in development before migrating"
        )


def _create_detection_history() -> None:
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
        sa.Column("scores", sa.JSON(), nullable=False),
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
        "ix_detection_history_device_id", "detection_history", ["device_id"]
    )
    op.create_index("ix_detection_history_user_id", "detection_history", ["user_id"])
    op.create_index(
        "ix_detection_history_timestamp", "detection_history", ["timestamp"]
    )
    op.create_index(
        "ix_detection_history_predicted_class",
        "detection_history",
        ["predicted_class"],
    )
    op.create_index(
        "ix_detection_history_confidence", "detection_history", ["confidence"]
    )


def _create_prediction_events() -> None:
    op.create_table(
        "prediction_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("history_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("predicted_class", sa.String(length=32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["history_id"], ["detection_history.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prediction_events_history_id", "prediction_events", ["history_id"]
    )
    op.create_index("ix_prediction_events_user_id", "prediction_events", ["user_id"])
    op.create_index(
        "ix_prediction_events_request_id", "prediction_events", ["request_id"]
    )
    op.create_index("ix_prediction_events_status", "prediction_events", ["status"])
    op.create_index(
        "ix_prediction_events_created_at", "prediction_events", ["created_at"]
    )


def _create_breed_profiles() -> None:
    op.create_table(
        "breed_profiles",
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
    op.create_index("ix_breed_profiles_slug", "breed_profiles", ["slug"])


def _create_breed_profile_revisions() -> None:
    op.create_table(
        "breed_profile_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("profile_id", sa.String(length=36), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("model_class", sa.String(length=32), nullable=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("strengths", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["profile_id"], ["breed_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "revision"),
    )
    op.create_index(
        "ix_breed_profile_revisions_profile_id",
        "breed_profile_revisions",
        ["profile_id"],
    )
    op.create_index(
        "ix_breed_profile_revisions_model_class",
        "breed_profile_revisions",
        ["model_class"],
    )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        raise RuntimeError(
            "The four-class migration rebuilds incompatible legacy data; "
            "run it only after an explicit data migration in a controlled deployment"
        )

    history_reset = _needs_replacement("detection_history", _HISTORY_COLUMNS)
    events_reset = history_reset or _needs_replacement(
        "prediction_events", _EVENT_COLUMNS
    )
    profile_reset = _needs_replacement("breed_profiles", _PROFILE_COLUMNS)
    revision_reset = _needs_replacement("breed_profile_revisions", _REVISION_COLUMNS)
    # Recreating a parent profile table requires recreating its child table too.
    revision_reset = revision_reset or profile_reset

    reset_tables = {
        table
        for table, should_reset in (
            ("detection_history", history_reset),
            ("prediction_events", events_reset),
            ("breed_profiles", profile_reset),
            ("breed_profile_revisions", revision_reset),
            ("disease_contents", _table_exists("disease_contents")),
            (
                "disease_content_revisions",
                _table_exists("disease_content_revisions"),
            ),
        )
        if should_reset
    }
    for table in reset_tables:
        _assert_safe_reset(table)

    # Drop dependants before their referenced tables and never retain disease-era rows.
    if events_reset:
        _drop_if_exists("prediction_events")
    if history_reset:
        _drop_if_exists("detection_history")
    if history_reset:
        _create_detection_history()
    if events_reset:
        _create_prediction_events()

    _drop_if_exists("disease_content_revisions")
    _drop_if_exists("disease_contents")
    if revision_reset:
        _drop_if_exists("breed_profile_revisions")
    if profile_reset:
        _drop_if_exists("breed_profiles")
    if profile_reset:
        _create_breed_profiles()
    if revision_reset:
        _create_breed_profile_revisions()


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade would recreate incompatible disease columns and is intentionally unsupported"
    )
