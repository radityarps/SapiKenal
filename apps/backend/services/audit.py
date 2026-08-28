"""Append-only audit event helpers and admin observability projections."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from config import settings
from db.core import SessionLocal
from db.models import AuditLog, DetectionHistory, PredictionEvent
from sqlalchemy import select
from sqlalchemy.orm import Session
from utils.logger import get_logger

logger = get_logger(__name__)


def record_audit(
    db: Session,
    *,
    action: str,
    actor_user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request_id: str | None = None,
    ip_hash: str | None = None,
    changed_fields: dict[str, Any] | None = None,
    status: str = "success",
    reason: str | None = None,
) -> AuditLog:
    """Stage an audit row in the current transaction; callers commit it."""
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        ip_hash=ip_hash,
        changed_fields=changed_fields,
        status=status,
        reason=reason,
    )
    db.add(event)
    return event


def mask_device_id(device_id: str) -> str:
    """Return a stable, non-reversible short device reference for admin views."""
    digest = hashlib.sha256(
        f"{settings.admin_device_hash_salt}:{device_id}".encode()
    ).hexdigest()
    return digest[:8]


def _history_values(item: dict[str, Any]) -> dict[str, Any]:
    try:
        timestamp = int(item["timestamp"])
        confidence = float(item["confidence"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid history metadata") from exc
    scores = item.get("scores") or {}
    try:
        normalized_scores = {
            "score_healthy": float(scores.get("healthy", 0)),
            "score_fmd": float(scores.get("FMD", 0)),
            "score_lsd": float(scores.get("LSD", 0)),
            "score_non_cattle": float(scores.get("non_cattle", 0)),
        }
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid history scores") from exc
    return {
        "device_id": str(item["device_id"]),
        "local_id": item.get("local_id"),
        "timestamp": timestamp,
        "predicted_class": str(item["predicted_class"]),
        "display_label": str(item["display_label"]),
        "confidence": confidence,
        **normalized_scores,
        "outcome": str(item.get("outcome", "accepted")),
        "rejection_reason": item.get("rejection_reason"),
        "inference_mode": str(item["inference_mode"]),
        "is_reliable": bool(item["is_reliable"]),
        "processing_ms": item.get("processing_ms"),
        "app_version": item.get("app_version"),
        "model_version": item.get("model_version"),
    }


def sync_history_to_admin(item: dict[str, Any], user_id: str | None = None) -> None:
    """Best-effort copy of mobile metadata into the SQLAlchemy admin projection."""
    values = _history_values(item)
    try:
        with SessionLocal() as db:
            row = db.scalar(
                select(DetectionHistory).where(
                    DetectionHistory.device_id == values["device_id"],
                    DetectionHistory.local_id == values["local_id"],
                )
            )
            if row is None:
                db.add(DetectionHistory(**values, user_id=user_id))
            else:
                for key, value in values.items():
                    setattr(row, key, value)
                if user_id is not None:
                    row.user_id = user_id
            db.commit()
    except Exception:
        logger.exception("Unable to sync mobile history into admin projection")


def record_prediction_event(
    *,
    request_id: str,
    status: str,
    outcome: str | None = None,
    error_code: str | None = None,
    predicted_class: str | None = None,
    confidence: float | None = None,
    scores: dict[str, float] | None = None,
    processing_ms: float | None = None,
    model_version: str | None = None,
    user_id: str | None = None,
) -> None:
    """Persist sanitized prediction observability without retaining image bytes."""
    try:
        resolved_outcome = outcome or {
            "success": "accepted",
            "rejected": "rejected",
            "failed": "failed",
        }.get(status, "failed")
        with SessionLocal() as db:
            db.add(
                PredictionEvent(
                    request_id=request_id[:64],
                    status=status,
                    outcome=resolved_outcome,
                    error_code=error_code,
                    predicted_class=predicted_class,
                    confidence=confidence,
                    scores=scores,
                    processing_ms=(
                        round(processing_ms) if processing_ms is not None else None
                    ),
                    model_version=model_version,
                    user_id=user_id,
                )
            )
            db.commit()
    except Exception:
        logger.exception("Unable to record prediction event")


def period_start(period: str) -> int:
    """Return a millisecond epoch start for an allowed dashboard period."""
    durations = {
        "24h": 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
        "30d": 30 * 24 * 60 * 60,
    }
    if period not in durations:
        raise ValueError("Unsupported dashboard period")
    return round((time.time() - durations[period]) * 1_000)
