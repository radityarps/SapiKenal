"""Database models for the admin foundation and future admin features."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import sqlalchemy as sa  # pyright: ignore[reportMissingImports]

# pi-lens-ignore: python-hallucinated-import
from sqlalchemy import (  # pyright: ignore[reportMissingImports]
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (  # pyright: ignore[reportMissingImports]
    Mapped,
    mapped_column,
)

from db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def uuid_value() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="user", index=True
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", index=True
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_actor_action", "actor_user_id", "action"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed_fields: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )


class DetectionHistory(Base):
    """Admin projection of mobile breed-identification history metadata."""

    __tablename__ = "detection_history"
    __table_args__ = (
        UniqueConstraint(
            "device_id", "local_id", name="uq_detection_history_device_local"
        ),
        Index("ix_detection_history_timestamp", "timestamp"),
        Index("ix_detection_history_predicted_class", "predicted_class"),
        Index("ix_detection_history_confidence", "confidence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    local_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    timestamp: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(32), nullable=False)
    display_label: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    scores: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    inference_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    is_reliable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    app_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preprocessing_summary: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class PredictionEvent(Base):
    __tablename__ = "prediction_events"
    __table_args__ = ()

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    history_id: Mapped[int | None] = mapped_column(
        ForeignKey("detection_history.id"), nullable=True, index=True
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    predicted_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class BreedProfile(Base):
    __tablename__ = "breed_profiles"
    __table_args__ = (UniqueConstraint("slug", "locale"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="id-ID")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class BreedProfileRevision(Base):
    __tablename__ = "breed_profile_revisions"
    __table_args__ = (UniqueConstraint("profile_id", "revision"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    profile_id: Mapped[str] = mapped_column(
        ForeignKey("breed_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    model_class: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    strengths: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        Index(
            "uq_model_versions_one_active",
            "status",
            unique=True,
            sqlite_where=sa.text("status = 'active'"),
            postgresql_where=sa.text("status = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    version: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    artifact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="available", index=True
    )
    input_size: Mapped[int] = mapped_column(Integer, nullable=False, default=224)
    classes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rolled_back_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    activated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )


class ModelActivation(Base):
    __tablename__ = "model_activations"
    __table_args__ = (Index("ix_model_activations_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    model_version_id: Mapped[str] = mapped_column(
        ForeignKey("model_versions.id"), nullable=False, index=True
    )
    previous_model_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("model_versions.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
