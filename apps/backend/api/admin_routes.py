# ruff: noqa: B008
"""Protected admin MVP routes for operations, users, content, and models."""

from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from threading import RLock
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import CANONICAL_LABELS, canonicalize_label, settings
from db.core import get_db
from db.models import (
    AuditLog,
    BreedProfile,
    BreedProfileRevision,
    DetectionHistory,
    ModelActivation,
    ModelVersion,
    PredictionEvent,
    User,
)
from inference_server import (
    get_model_status,
    mark_model_unavailable,
    reload_active_model,
)
from model.registry import (  # pyright: ignore[reportMissingImports]
    artifact_name_for,
    registry_root,
    resolve_artifact_path,
)
from model.validation import (  # pyright: ignore[reportMissingImports]
    ModelContractError,
    ModelValidationError,
    ModelValidationUnavailable,
    expected_classes,
    sha256_file,
    validate_model_file,
)
from services.audit import mask_device_id, period_start, record_audit

from .admin_schemas import (  # pyright: ignore[reportMissingImports]
    AuditLogResponse,
    BreedProfilePatchRequest,
    BreedProfileRequest,
    BreedProfileResponse,
    BreedProfileRevisionResponse,
    ModelActivationRequest,
    ModelRegisterRequest,
    ModelVersionResponse,
    UserCreateRequest,
    UserMutationResponse,
    UserPatchRequest,
    UserResponse,
)
from .auth_dependencies import require_admin
from .auth_security import hash_password, revoke_all_sessions
from .errors import AdminAPIError
from .schemas import HistoryCreate, _canonical_scores

router = APIRouter(prefix="/api/admin", tags=["admin"])
content_router = APIRouter(prefix="/api/content", tags=["content"])

_PAGE_SIZE_MAX = 100
_ALLOWED_MODEL_CLASSES = set(CANONICAL_LABELS)
_MODEL_ACTIVATION_LOCK = RLock()
_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _ip_hash(request: Request) -> str | None:
    client = request.client.host if request.client else None
    return hashlib.sha256(client.encode("utf-8")).hexdigest() if client else None


def _page(page: int, page_size: int) -> tuple[int, int]:
    return max(page, 1), min(max(page_size, 1), _PAGE_SIZE_MAX)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _user_response(user: User) -> dict[str, Any]:
    return UserResponse.model_validate(user).model_dump(mode="json")


def _audit_response(
    event: AuditLog, actor_display_name: str | None = None
) -> dict[str, Any]:
    response = AuditLogResponse.model_validate(event)
    return response.model_copy(
        update={"actor_display_name": actor_display_name}
    ).model_dump(mode="json")


def _model_response(model: ModelVersion) -> dict[str, Any]:
    response = ModelVersionResponse.model_validate(model).model_dump(mode="json")
    response["compatible"] = model.classes == expected_classes()
    return response


def _prediction_response(row: DetectionHistory) -> dict[str, Any]:
    try:
        scores = _canonical_scores(row.scores)
    except (TypeError, ValueError):
        scores = {}
    predicted_class = (
        row.predicted_class if row.predicted_class in CANONICAL_LABELS else "unknown"
    )
    return {
        "id": row.id,
        "device_ref": mask_device_id(row.device_id),
        "user_id": row.user_id,
        "timestamp": row.timestamp,
        "predicted_class": predicted_class,
        "display_label": row.display_label
        if predicted_class != "unknown"
        else "Tidak tersedia",
        "confidence": row.confidence
        if math.isfinite(row.confidence) and 0 <= row.confidence <= 1
        else 0.0,
        "scores": scores,
        "is_reliable": row.is_reliable,
        "inference_mode": row.inference_mode,
        "processing_ms": row.processing_ms,
        "app_version": row.app_version,
        "model_version": row.model_version,
        "status": "success",
        "error_code": None,
    }


def _event_status(event: PredictionEvent) -> str:
    return "success" if str(event.status).casefold() == "success" else "failed"


def _event_scores(event: PredictionEvent) -> dict[str, float]:
    """Return only a complete, contract-valid score object."""
    if event.predicted_class not in CANONICAL_LABELS or event.confidence is None:
        return {}
    try:
        return HistoryCreate.model_validate(
            {
                "device_id": "audit-event",
                "timestamp": 0,
                "predicted_class": event.predicted_class,
                "display_label": event.predicted_class,
                "confidence": event.confidence,
                "scores": event.scores,
                "inference_mode": "online",
                "is_reliable": False,
            }
        ).scores
    except (TypeError, ValueError):
        return {}


def _prediction_event_response(event: PredictionEvent) -> dict[str, Any]:
    is_failed = _event_status(event) == "failed"
    predicted_class: str | None = (
        event.predicted_class if event.predicted_class in CANONICAL_LABELS else None
    )
    try:
        confidence = float(event.confidence) if event.confidence is not None else 0.0
    except (TypeError, ValueError):
        confidence = 0.0
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        confidence = 0.0
    display_labels = {
        "bali": "Bali",
        "brahman": "Brahman",
        "brangus": "Brangus",
        "limusin": "Limusin",
    }
    display_label = (
        "Gagal teknis"
        if is_failed
        else display_labels.get(predicted_class or "", "Tidak tersedia")
    )
    return {
        "id": event.id,
        "device_ref": mask_device_id(event.request_id),
        "user_id": event.user_id,
        "timestamp": _event_timestamp_ms(event),
        "predicted_class": predicted_class or "unknown",
        "display_label": display_label,
        "confidence": confidence,
        "scores": _event_scores(event),
        "is_reliable": not is_failed and confidence >= settings.confidence_threshold,
        "inference_mode": "online",
        "processing_ms": event.processing_ms,
        "app_version": None,
        "model_version": event.model_version,
        "status": "failed" if is_failed else "success",
        "error_code": event.error_code,
    }


def _event_timestamp_ms(event: PredictionEvent) -> int:
    if event.created_at is None:
        return 0
    created_at = event.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return round(created_at.timestamp() * 1_000)


def _event_matches_history(event: PredictionEvent, row: DetectionHistory) -> bool:
    """Identify an online event later mirrored by mobile history sync."""
    if _event_status(event) != "success":
        return False
    if event.history_id is not None:
        return event.history_id == row.id
    if row.inference_mode.casefold() not in {"online", "backend"}:
        return False
    if event.predicted_class != row.predicted_class:
        return False
    try:
        if abs(_event_timestamp_ms(event) - row.timestamp) > 10 * 60 * 1_000:
            return False
        if (
            event.confidence is None
            or abs(float(event.confidence) - float(row.confidence)) > 0.01
        ):
            return False
        if (
            event.processing_ms is not None
            and row.processing_ms is not None
            and abs(float(event.processing_ms) - float(row.processing_ms)) > 1_000
        ):
            return False
        event_scores = _event_scores(event)
        row_scores = _canonical_scores(row.scores)
    except (TypeError, ValueError):
        return False
    return bool(event_scores) and all(
        abs(event_scores[label] - row_scores[label]) <= 0.01
        for label in CANONICAL_LABELS
    )


def _prediction_sources(
    db: Session,
    *,
    date_from: int | None = None,
    date_to: int | None = None,
) -> list[tuple[dict[str, Any], DetectionHistory | PredictionEvent]]:
    history_filters: list[Any] = []
    event_filters: list[Any] = [PredictionEvent.status.in_(["success", "failed"])]
    if date_from is not None:
        history_filters.append(DetectionHistory.timestamp >= date_from)
        event_filters.append(
            PredictionEvent.created_at
            >= datetime.fromtimestamp(date_from / 1_000, timezone.utc)
        )
    if date_to is not None:
        history_filters.append(DetectionHistory.timestamp <= date_to)
        event_filters.append(
            PredictionEvent.created_at
            <= datetime.fromtimestamp(date_to / 1_000, timezone.utc)
        )

    histories = db.scalars(select(DetectionHistory).where(*history_filters)).all()
    events = db.scalars(select(PredictionEvent).where(*event_filters)).all()
    sources: list[tuple[dict[str, Any], DetectionHistory | PredictionEvent]] = [
        (_prediction_response(row), row) for row in histories
    ]
    for event in events:
        if _event_status(event) == "success" and any(
            _event_matches_history(event, row) for row in histories
        ):
            continue
        sources.append((_prediction_event_response(event), event))
    return sources


def _matches_prediction_filters(
    item: dict[str, Any],
    source: DetectionHistory | PredictionEvent,
    *,
    search: str | None,
    predicted_class: str | None,
    status: str | None,
    min_confidence: float | None,
    max_confidence: float | None,
    reliable: bool | None,
    inference_mode: str | None,
    model_version: str | None,
) -> bool:
    if search:
        search_values = [
            item.get("display_label"),
            item.get("predicted_class"),
            item.get("inference_mode"),
            item.get("model_version"),
            item.get("app_version"),
            item.get("user_id"),
        ]
        if isinstance(source, PredictionEvent):
            search_values.extend([source.error_code, source.request_id])
        term = search.strip().casefold()
        if not any(term in str(value or "").casefold() for value in search_values):
            return False
    if predicted_class and item["predicted_class"] != predicted_class:
        return False
    if status and item["status"] != status:
        return False
    if min_confidence is not None and item["confidence"] < min_confidence:
        return False
    if max_confidence is not None and item["confidence"] > max_confidence:
        return False
    if reliable is not None and item["is_reliable"] != reliable:
        return False
    if (
        inference_mode
        and item["inference_mode"].casefold() != inference_mode.casefold()
    ):
        return False
    return not model_version or item["model_version"] == model_version


def _latest_revision(db: Session, profile_id: str) -> BreedProfileRevision | None:
    return db.scalar(
        select(BreedProfileRevision)
        .where(BreedProfileRevision.profile_id == profile_id)
        .order_by(desc(BreedProfileRevision.revision))
    )


def _profile_response(
    profile: BreedProfile, revision: BreedProfileRevision
) -> dict[str, Any]:
    return BreedProfileResponse(
        id=profile.id,
        slug=profile.slug,
        locale=profile.locale,
        status=profile.status,
        revision=BreedProfileRevisionResponse.model_validate(revision),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    ).model_dump(mode="json")


def _active_model(db: Session) -> ModelVersion | None:
    return db.scalar(
        select(ModelVersion)
        .where(ModelVersion.status == "active")
        .order_by(desc(ModelVersion.activated_at))
    )


def _model_path(model: ModelVersion) -> Path:
    try:
        return resolve_artifact_path(model.artifact_name)
    except ValueError as exc:
        raise AdminAPIError(422, "MODEL_ARTIFACT_INVALID", str(exc)) from exc


def _validate_model_artifact(model: ModelVersion) -> Path:
    path = _model_path(model)
    if not path.is_file() or path.suffix.casefold() != ".keras":
        raise AdminAPIError(
            422, "MODEL_ARTIFACT_INVALID", "Model artifact is unavailable"
        )
    digest = sha256_file(path)
    if digest.casefold() != model.checksum.casefold():
        raise AdminAPIError(
            422, "MODEL_ARTIFACT_INVALID", "Model checksum does not match"
        )
    if model.classes != expected_classes():
        raise AdminAPIError(
            422,
            "MODEL_CONTRACT_MISMATCH",
            "Model classes do not match the configured output order",
        )
    return path


def _canonical_model_classes(classes: list[str]) -> list[str]:
    normalized = [canonicalize_label(item) for item in classes]
    if normalized != expected_classes():
        raise AdminAPIError(
            422,
            "MODEL_CONTRACT_MISMATCH",
            "Model classes must match the configured order: "
            + ", ".join(expected_classes()),
        )
    return normalized


def _parse_upload_classes(raw_classes: str) -> list[str]:
    value = raw_classes.strip()
    if not value:
        return expected_classes()
    try:
        parsed = json.loads(value) if value.startswith("[") else value.split(",")
    except json.JSONDecodeError as exc:
        raise AdminAPIError(
            422, "MODEL_CONTRACT_MISMATCH", "Model classes must be valid"
        ) from exc
    if not isinstance(parsed, list) or not all(
        isinstance(item, str) for item in parsed
    ):
        raise AdminAPIError(
            422, "MODEL_CONTRACT_MISMATCH", "Model classes must be valid"
        )
    return _canonical_model_classes([item.strip() for item in parsed if item.strip()])


def _record_upload_failure(
    db: Session,
    request: Request,
    admin: User,
    version: str,
    code: str,
) -> None:
    try:
        record_audit(
            db,
            action="model_upload_failed",
            actor_user_id=admin.id,
            resource_type="model_version",
            resource_id=version[:128],
            request_id=_request_id(request),
            ip_hash=_ip_hash(request),
            status="failed",
            changed_fields={"error_code": code},
        )
        db.commit()
    except Exception:
        db.rollback()


def _record_model_failure(
    db: Session,
    request: Request,
    actor: User,
    model: ModelVersion,
    action: str,
    reason: str,
    message: str,
    previous: ModelVersion | None = None,
) -> None:
    db.add(
        ModelActivation(
            model_version_id=model.id,
            previous_model_version_id=previous.id if previous else None,
            action=action,
            reason=reason,
            status="failed",
            actor_user_id=actor.id,
            error_message=message[:256],
        )
    )
    record_audit(
        db,
        action=f"model_{action}_failed",
        actor_user_id=actor.id,
        resource_type="model_version",
        resource_id=model.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        status="failed",
        reason=reason,
    )
    db.commit()


@router.get("/access")
def admin_access_check(user: User = Depends(require_admin)):
    """Return the authenticated admin identity for shell/web smoke tests."""
    return {
        "status": "success",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
        },
    }


@router.get("/dashboard")
def dashboard(
    period: Literal["24h", "7d", "30d"] = Query(default="7d"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Return operational aggregates without exposing images or raw devices."""
    start = period_start(period)
    end = round(datetime.now(timezone.utc).timestamp() * 1_000)
    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    users_active = (
        db.scalar(select(func.count()).select_from(User).where(User.status == "active"))
        or 0
    )
    prediction_items = [
        item
        for item, _source in _prediction_sources(
            db,
            date_from=start,
            date_to=end,
        )
    ]
    accepted_items = [item for item in prediction_items if item["status"] == "success"]
    failures = sum(1 for item in prediction_items if item["status"] == "failed")
    accepted = len(accepted_items)
    distribution: dict[str, int] = dict.fromkeys(CANONICAL_LABELS, 0)
    for item in accepted_items:
        label = str(item["predicted_class"])
        if label in distribution:
            distribution[label] += 1
    low_confidence = sum(
        1
        for item in accepted_items
        if item["confidence"] < settings.confidence_threshold
    )
    timings = [
        _safe_int(item["processing_ms"])
        for item in prediction_items
        if item["processing_ms"] is not None
    ]
    timings.sort()
    p95 = timings[max(0, math.ceil(len(timings) * 0.95) - 1)] if timings else None
    attempts = accepted + failures
    active_model = _active_model(db)
    recent_audits = db.scalars(
        select(AuditLog).order_by(desc(AuditLog.created_at)).limit(5)
    ).all()
    health = get_model_status()
    return {
        "status": "success",
        "period": {"key": period, "start_timestamp": start, "end_timestamp": end},
        "users": {"total": _safe_int(users_total), "active": _safe_int(users_active)},
        "predictions": {
            "total": _safe_int(accepted),
            "attempts": _safe_int(attempts),
            "accepted": _safe_int(accepted),
            "distribution": distribution,
            "low_confidence": _safe_int(low_confidence),
            "low_confidence_rate": (low_confidence / accepted if accepted else None),
            "failures": _safe_int(failures),
            "median_processing_ms": median(timings) if timings else None,
            "p95_processing_ms": p95,
        },
        "model": {
            "version": active_model.version if active_model else settings.model_version,
            "activated_at": active_model.activated_at if active_model else None,
            "status": active_model.status
            if active_model
            else ("active" if health["model_loaded"] else "degraded"),
        },
        "health": {
            "status": (
                "ok"
                if health["model_loaded"]
                and active_model is not None
                and health.get("model_version") == active_model.version
                else "degraded"
            ),
            "model_loaded": health["model_loaded"],
            "model_version": health.get("model_version", settings.model_version),
            "desired_model_version": active_model.version if active_model else None,
        },
        "recent_audit_events": [_audit_response(event) for event in recent_audits],
    }


@router.get("/users")
def list_users(
    search: str | None = Query(default=None, max_length=120),
    role: Literal["user", "admin"] | None = None,
    status: Literal["active", "inactive", "locked"] | None = None,
    sort_by: Literal[
        "created_at", "email", "display_name", "last_login_at"
    ] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    filters = []
    if search:
        term = f"%{search.strip().casefold()}%"
        filters.append(
            (func.lower(User.email).like(term))
            | (func.lower(User.display_name).like(term))
        )
    if role:
        filters.append(User.role == role)
    if status:
        filters.append(User.status == status)
    order_column = {
        "created_at": User.created_at,
        "email": User.email,
        "display_name": User.display_name,
        "last_login_at": User.last_login_at,
    }[sort_by]
    order = asc(order_column) if sort_order == "asc" else desc(order_column)
    total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    items = db.scalars(
        select(User)
        .where(*filters)
        .order_by(order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": _safe_int(total),
        "items": [_user_response(item) for item in items],
    }


@router.post("/users", response_model=UserMutationResponse, status_code=201)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    email = str(payload.email).strip().casefold()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise AdminAPIError(409, "EMAIL_EXISTS", "Email is already registered")
    temporary_password = payload.password or secrets.token_urlsafe(12)
    try:
        password_hash = hash_password(temporary_password)
    except ValueError as exc:
        raise AdminAPIError(422, "WEAK_PASSWORD", str(exc)) from exc
    user = User(
        email=email,
        password_hash=password_hash,
        display_name=payload.display_name.strip(),
        role=payload.role,
        status="active",
        must_change_password=payload.password is None,
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(user)
    db.flush()
    record_audit(
        db,
        action="user_created",
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=user.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={
            "email": "set",
            "display_name": "set",
            "role": "set",
            "status": "set",
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AdminAPIError(409, "EMAIL_EXISTS", "Email is already registered") from exc
    return {
        "status": "success",
        "user": _user_response(user),
        "temporary_password": temporary_password if payload.password is None else None,
    }


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise AdminAPIError(404, "USER_NOT_FOUND", "User not found")
    return {"status": "success", "user": _user_response(user)}


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: UserPatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = db.get(User, user_id)
    if target is None:
        raise AdminAPIError(404, "USER_NOT_FOUND", "User not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise AdminAPIError(422, "NO_CHANGES", "At least one field must be changed")
    if target.id == admin.id and (
        changes.get("role") == "user" or changes.get("status") in {"inactive", "locked"}
    ):
        raise AdminAPIError(
            409, "SELF_ADMIN_GUARD", "An admin cannot remove their own access"
        )
    demotes_last_admin = (
        target.role == "admin"
        and target.status == "active"
        and (
            changes.get("role", target.role) != "admin"
            or changes.get("status", target.status) != "active"
        )
    )
    if demotes_last_admin:
        active_admins = (
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == "admin", User.status == "active")
            )
            or 0
        )
        if active_admins <= 1:
            raise AdminAPIError(
                409, "LAST_ADMIN_GUARD", "The last active admin cannot be removed"
            )
    changed_fields = {}
    for field in ("display_name", "role", "status"):
        if field in changes:
            value = (
                changes[field].strip() if field == "display_name" else changes[field]
            )
            setattr(target, field, value)
            changed_fields[field] = "changed"
    target.updated_by = admin.id
    record_audit(
        db,
        action="user_updated",
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=target.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields=changed_fields,
    )
    db.commit()
    return {"status": "success", "user": _user_response(target)}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    target = db.get(User, user_id)
    if target is None:
        raise AdminAPIError(404, "USER_NOT_FOUND", "User not found")
    temporary_password = secrets.token_urlsafe(12)
    target.password_hash = hash_password(temporary_password)
    target.must_change_password = True
    revoked_sessions = revoke_all_sessions(target.id, db)
    record_audit(
        db,
        action="user_password_reset",
        actor_user_id=admin.id,
        resource_type="user",
        resource_id=target.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={
            "password": "changed",
            "must_change_password": "set",
            "revoked_sessions": revoked_sessions,
        },
    )
    db.commit()
    return {
        "status": "success",
        "user": _user_response(target),
        "temporary_password": temporary_password,
    }


@router.get("/predictions")
def list_predictions(
    search: str | None = Query(default=None, max_length=120),
    predicted_class: Literal["bali", "brahman", "brangus", "limusin"] | None = None,
    status: Literal["success", "failed"] | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=1),
    max_confidence: float | None = Query(default=None, ge=0, le=1),
    reliable: bool | None = None,
    inference_mode: str | None = Query(default=None, max_length=32),
    model_version: str | None = Query(default=None, max_length=128),
    date_from: int | None = Query(default=None, ge=0),
    date_to: int | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    filtered_sources = [
        (item, source)
        for item, source in _prediction_sources(
            db,
            date_from=date_from,
            date_to=date_to,
        )
        if _matches_prediction_filters(
            item,
            source,
            search=search,
            predicted_class=predicted_class,
            status=status,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            reliable=reliable,
            inference_mode=inference_mode,
            model_version=model_version,
        )
    ]
    filtered_sources.sort(key=lambda source: source[0]["timestamp"], reverse=True)
    start_index = (page - 1) * page_size
    items = [
        item
        for item, _source in filtered_sources[start_index : start_index + page_size]
    ]
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": len(filtered_sources),
        "items": items,
    }


@router.get("/predictions/{prediction_id}")
def get_prediction(
    prediction_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    try:
        row = db.get(DetectionHistory, int(prediction_id))
    except (TypeError, ValueError):
        row = None
    if row is not None:
        return {"status": "success", "item": _prediction_response(row)}

    event = db.get(PredictionEvent, prediction_id)
    if event is not None and _event_status(event) in {"success", "failed"}:
        return {"status": "success", "item": _prediction_event_response(event)}
    raise AdminAPIError(404, "PREDICTION_NOT_FOUND", "Prediction metadata not found")


@router.get("/profiles")
def list_profiles(
    status: Literal["draft", "active", "inactive"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    filters = [BreedProfile.status == status] if status else []
    total = (
        db.scalar(select(func.count()).select_from(BreedProfile).where(*filters)) or 0
    )
    profiles = db.scalars(
        select(BreedProfile)
        .where(*filters)
        .order_by(asc(BreedProfile.slug))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = []
    for profile in profiles:
        revision = _latest_revision(db, profile.id)
        if revision is not None:
            items.append(_profile_response(profile, revision))
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": _safe_int(total),
        "items": items,
    }


@router.post("/profiles", status_code=201)
def create_profile(
    payload: BreedProfileRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if (
        payload.model_class is not None
        and payload.model_class not in _ALLOWED_MODEL_CLASSES
    ):
        raise AdminAPIError(422, "INVALID_MODEL_CLASS", "Unknown model class")
    if (
        db.scalar(
            select(BreedProfile).where(
                BreedProfile.slug == payload.slug,
                BreedProfile.locale == payload.locale,
            )
        )
        is not None
    ):
        raise AdminAPIError(409, "PROFILE_EXISTS", "Breed profile already exists")
    profile = BreedProfile(
        slug=payload.slug,
        locale=payload.locale,
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(profile)
    db.flush()
    revision = BreedProfileRevision(
        profile_id=profile.id,
        revision=1,
        model_class=payload.model_class,
        display_name=payload.display_name.strip(),
        summary=payload.summary.strip(),
        strengths=payload.strengths.strip(),
        limitations=payload.limitations.strip(),
        disclaimer=payload.disclaimer.strip(),
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(revision)
    record_audit(
        db,
        action="breed_profile_created",
        actor_user_id=admin.id,
        resource_type="breed_profile",
        resource_id=profile.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"slug": "set", "revision": "created", "status": "draft"},
    )
    db.commit()
    return {"status": "success", "item": _profile_response(profile, revision)}


@router.get("/profiles/{profile_id}")
def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    profile = db.get(BreedProfile, profile_id)
    revision = _latest_revision(db, profile_id) if profile else None
    if profile is None or revision is None:
        raise AdminAPIError(404, "PROFILE_NOT_FOUND", "Breed profile not found")
    return {"status": "success", "item": _profile_response(profile, revision)}


@router.patch("/profiles/{profile_id}")
def update_profile(
    profile_id: str,
    payload: BreedProfilePatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    profile = db.get(BreedProfile, profile_id)
    current = _latest_revision(db, profile_id) if profile else None
    if profile is None or current is None:
        raise AdminAPIError(404, "PROFILE_NOT_FOUND", "Breed profile not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise AdminAPIError(422, "NO_CHANGES", "At least one field must be changed")
    if "model_class" in changes and changes[
        "model_class"
    ] not in _ALLOWED_MODEL_CLASSES | {None}:
        raise AdminAPIError(422, "INVALID_MODEL_CLASS", "Unknown model class")
    values = {
        "model_class": current.model_class,
        "display_name": current.display_name,
        "summary": current.summary,
        "strengths": current.strengths,
        "limitations": current.limitations,
        "disclaimer": current.disclaimer,
    }
    values.update(changes)
    revision = BreedProfileRevision(
        profile_id=profile.id,
        revision=current.revision + 1,
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
        **values,
    )
    db.add(revision)
    profile.status = "draft"
    profile.updated_by = admin.id
    record_audit(
        db,
        action="breed_profile_updated",
        actor_user_id=admin.id,
        resource_type="breed_profile",
        resource_id=profile.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields=dict.fromkeys(changes, "changed"),
    )
    db.commit()
    return {"status": "success", "item": _profile_response(profile, revision)}


@router.post("/profiles/{profile_id}/activate")
def activate_profile(
    profile_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    profile = db.get(BreedProfile, profile_id)
    revision = _latest_revision(db, profile_id) if profile else None
    if profile is None or revision is None:
        raise AdminAPIError(404, "PROFILE_NOT_FOUND", "Breed profile not found")
    if (
        not revision.disclaimer.strip()
        or not revision.strengths.strip()
        or not revision.limitations.strip()
    ):
        raise AdminAPIError(
            422,
            "PROFILE_CONTENT_INCOMPLETE",
            "Disclaimer, strengths, and limitations are required",
        )
    for previous_revision in db.scalars(
        select(BreedProfileRevision).where(
            BreedProfileRevision.profile_id == profile.id,
            BreedProfileRevision.status == "active",
        )
    ).all():
        previous_revision.status = "inactive"
    revision.status = "active"
    profile.status = "active"
    profile.updated_by = admin.id
    record_audit(
        db,
        action="breed_profile_activated",
        actor_user_id=admin.id,
        resource_type="breed_profile",
        resource_id=profile.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"status": "active", "revision": revision.revision},
    )
    db.commit()
    return {"status": "success", "item": _profile_response(profile, revision)}


@router.post("/profiles/{profile_id}/deactivate")
def deactivate_profile(
    profile_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    profile = db.get(BreedProfile, profile_id)
    revision = _latest_revision(db, profile_id) if profile else None
    if profile is None or revision is None:
        raise AdminAPIError(404, "PROFILE_NOT_FOUND", "Breed profile not found")
    profile.status = "inactive"
    profile.updated_by = admin.id
    if revision.status == "active":
        revision.status = "inactive"
    record_audit(
        db,
        action="breed_profile_deactivated",
        actor_user_id=admin.id,
        resource_type="breed_profile",
        resource_id=profile.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"status": "inactive"},
    )
    db.commit()
    return {"status": "success", "item": _profile_response(profile, revision)}


@content_router.get("/profiles")
def public_profiles(db: Session = Depends(get_db)):
    """Return only active breed profiles for mobile consumption."""
    profiles = db.scalars(
        select(BreedProfile)
        .where(BreedProfile.status == "active")
        .order_by(asc(BreedProfile.slug))
    ).all()
    items = []
    for profile in profiles:
        revision = db.scalar(
            select(BreedProfileRevision).where(
                BreedProfileRevision.profile_id == profile.id,
                BreedProfileRevision.status == "active",
            )
        )
        if revision is None:
            continue
        items.append(
            {
                "slug": profile.slug,
                "locale": profile.locale,
                "model_class": revision.model_class,
                "display_name": revision.display_name,
                "summary": revision.summary,
                "strengths": revision.strengths,
                "limitations": revision.limitations,
                "disclaimer": revision.disclaimer,
                "revision": revision.revision,
            }
        )
    return {"status": "success", "items": items}


@router.get("/models")
def list_models(
    search: str | None = Query(default=None, max_length=128),
    status: str | None = Query(default=None, max_length=16),
    registered_from: datetime | None = None,
    registered_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    filters = []
    if search and (search := search.strip()):
        pattern = f"%{search}%"
        filters.append(
            or_(
                ModelVersion.version.ilike(pattern),
                ModelVersion.artifact_name.ilike(pattern),
                ModelVersion.notes.ilike(pattern),
            )
        )
    if status:
        filters.append(ModelVersion.status == status)
    if registered_from:
        filters.append(ModelVersion.registered_at >= registered_from)
    if registered_to:
        filters.append(ModelVersion.registered_at <= registered_to)
    query = select(ModelVersion).where(*filters)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(desc(ModelVersion.registered_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    active = _active_model(db)
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": _safe_int(total),
        "active_version": active.version if active else settings.model_version,
        "expected_classes": expected_classes(),
        "items": [_model_response(item) for item in items],
    }


@router.post("/models/upload", status_code=201)
async def upload_model(
    request: Request,
    version: str = Form(...),
    artifact: UploadFile | None = File(default=None),
    input_size: int = Form(default=settings.input_size),
    classes: str = Form(default=""),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Stream, validate, and register a private server model artifact."""
    version = version.strip()
    if not version or len(version) > 128:
        _record_upload_failure(db, request, admin, version, "MODEL_VERSION_INVALID")
        raise AdminAPIError(
            422, "MODEL_VERSION_INVALID", "Model version must be 1-128 characters"
        )
    if artifact is None or not artifact.filename:
        _record_upload_failure(db, request, admin, version, "MODEL_UPLOAD_REQUIRED")
        raise AdminAPIError(400, "MODEL_UPLOAD_REQUIRED", "Model file is required")
    filename = artifact.filename
    if "/" in filename.replace("\\", "/"):
        _record_upload_failure(db, request, admin, version, "MODEL_FILE_NAME_INVALID")
        raise AdminAPIError(
            400,
            "MODEL_FILE_NAME_INVALID",
            "Model filename must not contain path separators",
        )
    if not filename.casefold().endswith(".keras"):
        _record_upload_failure(db, request, admin, version, "MODEL_FILE_TYPE_INVALID")
        raise AdminAPIError(
            400, "MODEL_FILE_TYPE_INVALID", "Only .keras model artifacts are accepted"
        )
    if (
        db.scalar(select(ModelVersion).where(ModelVersion.version == version))
        is not None
    ):
        _record_upload_failure(db, request, admin, version, "MODEL_VERSION_EXISTS")
        raise AdminAPIError(409, "MODEL_VERSION_EXISTS", "Model version already exists")

    content_length = request.headers.get("content-length")
    declared_length: int | None = None
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError:
            declared_length = None
    if (
        declared_length is not None
        and declared_length > settings.model_upload_max_bytes + 1_048_576
    ):
        _record_upload_failure(db, request, admin, version, "MODEL_FILE_TOO_LARGE")
        raise AdminAPIError(
            413, "MODEL_FILE_TOO_LARGE", "Model file exceeds the upload limit"
        )

    try:
        model_classes = _parse_upload_classes(classes)
    except AdminAPIError as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        _record_upload_failure(
            db,
            request,
            admin,
            version,
            str(detail.get("code", "MODEL_CONTRACT_MISMATCH")),
        )
        raise
    model_notes = notes.strip() if notes else None
    if len(model_notes or "") > 10_000:
        _record_upload_failure(db, request, admin, version, "MODEL_NOTES_INVALID")
        raise AdminAPIError(
            422, "MODEL_NOTES_INVALID", "Model notes must not exceed 10000 characters"
        )
    temporary_path: Path | None = None
    final_path: Path | None = None
    moved = False
    persisted = False
    try:
        root = registry_root(create=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=root,
            prefix=".model-upload-",
            suffix=".keras",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            size = 0
            digest = hashlib.sha256()
            while True:
                chunk = await artifact.read(_UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.model_upload_max_bytes:
                    raise AdminAPIError(
                        413,
                        "MODEL_FILE_TOO_LARGE",
                        "Model file exceeds the upload limit",
                    )
                temporary.write(chunk)
                digest.update(chunk)

        if size <= 0:
            raise AdminAPIError(400, "MODEL_UPLOAD_REQUIRED", "Model file is empty")

        if temporary_path is None:
            raise AdminAPIError(
                500, "MODEL_UPLOAD_FAILED", "Model upload could not be completed"
            )
        upload_checksum = digest.hexdigest()
        metadata = validate_model_file(
            temporary_path,
            input_size=input_size,
            classes=model_classes,
        )
        validated_checksum = metadata.get("checksum")
        if (
            validated_checksum is not None
            and str(validated_checksum).casefold() != upload_checksum.casefold()
        ):
            raise ModelValidationError("Model checksum changed during validation")
        checksum = upload_checksum
        artifact_name = artifact_name_for(version, checksum)
        candidate_path = root / artifact_name
        if candidate_path.exists() or candidate_path.is_symlink():
            raise AdminAPIError(
                409, "MODEL_ARTIFACT_EXISTS", "Model artifact already exists"
            )
        try:
            os.link(temporary_path, candidate_path, follow_symlinks=False)
        except FileExistsError as exc:
            raise AdminAPIError(
                409, "MODEL_ARTIFACT_EXISTS", "Model artifact already exists"
            ) from exc
        final_path = candidate_path
        moved = True
        temporary_path.unlink(missing_ok=True)

        model = ModelVersion(
            version=version,
            artifact_name=artifact_name,
            checksum=checksum,
            status="available",
            input_size=input_size,
            classes=model_classes,
            notes=model_notes,
            registered_by=admin.id,
        )
        db.add(model)
        db.flush()
        record_audit(
            db,
            action="model_uploaded",
            actor_user_id=admin.id,
            resource_type="model_version",
            resource_id=model.id,
            request_id=_request_id(request),
            ip_hash=_ip_hash(request),
            changed_fields={
                "version": version,
                "artifact": artifact_name,
                "checksum": checksum,
            },
        )
        db.commit()
        persisted = True
        return {"status": "success", "item": _model_response(model)}
    except ModelValidationUnavailable as exc:
        db.rollback()
        _record_upload_failure(
            db, request, admin, version, "MODEL_VALIDATOR_UNAVAILABLE"
        )
        raise AdminAPIError(
            503,
            "MODEL_VALIDATOR_UNAVAILABLE",
            "Model validation is unavailable on this backend",
        ) from exc
    except ModelContractError as exc:
        db.rollback()
        _record_upload_failure(db, request, admin, version, "MODEL_CONTRACT_MISMATCH")
        raise AdminAPIError(
            422,
            "MODEL_CONTRACT_MISMATCH",
            str(exc)[:256],
        ) from exc
    except ModelValidationError as exc:
        db.rollback()
        _record_upload_failure(db, request, admin, version, "MODEL_ARTIFACT_INVALID")
        raise AdminAPIError(
            422,
            "MODEL_ARTIFACT_INVALID",
            str(exc)[:256],
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        _record_upload_failure(db, request, admin, version, "MODEL_VERSION_EXISTS")
        raise AdminAPIError(
            409, "MODEL_VERSION_EXISTS", "Model version already exists"
        ) from exc
    except AdminAPIError as exc:
        db.rollback()
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        _record_upload_failure(
            db,
            request,
            admin,
            version,
            str(detail.get("code", "MODEL_UPLOAD_FAILED")),
        )
        raise
    except Exception as exc:
        db.rollback()
        _record_upload_failure(db, request, admin, version, "MODEL_UPLOAD_FAILED")
        raise AdminAPIError(
            500, "MODEL_UPLOAD_FAILED", "Model upload could not be completed"
        ) from exc
    finally:
        await artifact.close()
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
        if moved and not persisted and final_path is not None:
            final_path.unlink(missing_ok=True)


@router.post("/models/register", status_code=201)
def register_model(
    payload: ModelRegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if (
        db.scalar(select(ModelVersion).where(ModelVersion.version == payload.version))
        is not None
    ):
        raise AdminAPIError(409, "MODEL_VERSION_EXISTS", "Model version already exists")
    model_classes = _canonical_model_classes(payload.classes)
    model = ModelVersion(
        version=payload.version,
        artifact_name=payload.artifact_name,
        checksum=payload.checksum,
        status="available",
        input_size=payload.input_size,
        classes=model_classes,
        metrics=payload.metrics,
        notes=payload.notes,
        registered_by=admin.id,
    )
    db.add(model)
    db.flush()
    try:
        artifact_path = _validate_model_artifact(model)
        validate_model_file(
            artifact_path,
            input_size=model.input_size,
            classes=model.classes,
        )
    except AdminAPIError:
        db.rollback()
        raise
    except ModelValidationUnavailable as exc:
        db.rollback()
        raise AdminAPIError(
            503,
            "MODEL_VALIDATOR_UNAVAILABLE",
            "Model validation is unavailable on this backend",
        ) from exc
    except ModelContractError as exc:
        db.rollback()
        raise AdminAPIError(422, "MODEL_CONTRACT_MISMATCH", str(exc)[:256]) from exc
    except ModelValidationError as exc:
        db.rollback()
        raise AdminAPIError(422, "MODEL_ARTIFACT_INVALID", str(exc)[:256]) from exc
    record_audit(
        db,
        action="model_registered",
        actor_user_id=admin.id,
        resource_type="model_version",
        resource_id=model.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"version": "set", "artifact": "registered"},
    )
    db.commit()
    return {"status": "success", "item": _model_response(model)}


@router.get("/models/{model_id}")
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    model = db.get(ModelVersion, model_id)
    if model is None:
        raise AdminAPIError(404, "MODEL_NOT_FOUND", "Model version not found")
    return {"status": "success", "item": _model_response(model)}


def _restore_runtime_model(previous: ModelVersion | None) -> None:
    """Restore the previous runtime model after a failed registry commit."""
    if previous is None:
        mark_model_unavailable(
            "No previous model is available after activation failure"
        )
        return
    try:
        previous_path = _validate_model_artifact(previous)
        reload_active_model(
            previous_path,
            previous.version,
            previous.classes,
            previous.input_size,
        )
    except Exception as exc:
        mark_model_unavailable(f"Previous model restore failed: {exc!s}"[:256])


def _activate_model(
    model: ModelVersion,
    action: Literal["activate", "rollback"],
    reason: str,
    request: Request,
    db: Session,
    admin: User,
):
    with _MODEL_ACTIVATION_LOCK:
        previous = _active_model(db)

        if model.status == "active":
            _record_model_failure(
                db,
                request,
                admin,
                model,
                action,
                reason,
                "Model version is already active",
                previous,
            )
            raise AdminAPIError(
                409, "MODEL_ALREADY_ACTIVE", "Model version is already active"
            )

        expected_status = "available" if action == "activate" else "retired"
        if model.status != expected_status:
            message = (
                "Only available model versions can be activated"
                if action == "activate"
                else "Only retired model versions can be rolled back"
            )
            _record_model_failure(
                db, request, admin, model, action, reason, message, previous
            )
            raise AdminAPIError(
                409,
                "MODEL_LIFECYCLE_INVALID",
                message,
            )

        if action == "rollback":
            was_active = db.scalar(
                select(ModelActivation.id).where(
                    ModelActivation.model_version_id == model.id,
                    ModelActivation.status == "success",
                    ModelActivation.action.in_(["activate", "rollback"]),
                )
            )
            if was_active is None:
                message = "Model was never active"
                _record_model_failure(
                    db, request, admin, model, action, reason, message, previous
                )
                raise AdminAPIError(409, "MODEL_ROLLBACK_UNAVAILABLE", message)

        try:
            path = _validate_model_artifact(model)
        except AdminAPIError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            message = str(detail.get("message", "Model artifact validation failed"))
            _record_model_failure(
                db, request, admin, model, action, reason, message, previous
            )
            raise

        try:
            reload_active_model(
                path,
                model.version,
                model.classes,
                model.input_size,
            )
        except Exception as exc:
            _record_model_failure(
                db, request, admin, model, action, reason, str(exc), previous
            )
            raise AdminAPIError(
                422, "MODEL_ACTIVATION_FAILED", "Model validation or warm-up failed"
            ) from exc
        try:
            changed_at = datetime.now(timezone.utc)
            for active in db.scalars(
                select(ModelVersion).where(ModelVersion.status == "active")
            ).all():
                active.status = "retired"
                active.deactivated_at = changed_at
            db.flush()
            model.status = "active"
            model.activated_at = changed_at
            if action == "rollback":
                model.rolled_back_at = changed_at
            model.activated_by = admin.id
            db.add(
                ModelActivation(
                    model_version_id=model.id,
                    previous_model_version_id=previous.id if previous else None,
                    action=action,
                    reason=reason,
                    status="success",
                    actor_user_id=admin.id,
                )
            )
            record_audit(
                db,
                action=f"model_{action}",
                actor_user_id=admin.id,
                resource_type="model_version",
                resource_id=model.id,
                request_id=_request_id(request),
                ip_hash=_ip_hash(request),
                changed_fields={"active_version": model.version},
                reason=reason,
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            _restore_runtime_model(previous)
            try:
                _record_model_failure(
                    db, request, admin, model, action, reason, str(exc), previous
                )
            except Exception:
                db.rollback()
            raise AdminAPIError(
                500,
                "MODEL_ACTIVATION_COMMIT_FAILED",
                "Model activation could not be committed",
            ) from exc
        return {"status": "success", "item": _model_response(model)}


@router.post("/models/{model_id}/activate")
def activate_model(
    model_id: str,
    payload: ModelActivationRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    with _MODEL_ACTIVATION_LOCK:
        model = db.get(ModelVersion, model_id)
        if model is None:
            raise AdminAPIError(404, "MODEL_NOT_FOUND", "Model version not found")
        return _activate_model(model, "activate", payload.reason, request, db, admin)


@router.post("/models/{model_id}/rollback")
def rollback_model(
    model_id: str,
    payload: ModelActivationRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    with _MODEL_ACTIVATION_LOCK:
        model = db.get(ModelVersion, model_id)
        if model is None:
            raise AdminAPIError(404, "MODEL_NOT_FOUND", "Model version not found")
        return _activate_model(model, "rollback", payload.reason, request, db, admin)


@router.get("/audit-logs")
def list_audit_logs(
    search: str | None = Query(default=None, max_length=120),
    actor_user_id: str | None = None,
    action: str | None = Query(default=None, max_length=64),
    resource_type: str | None = Query(default=None, max_length=64),
    status: Literal["success", "failed"] | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    filters = []
    if search:
        term = f"%{search.strip().casefold()}%"
        filters.append(
            func.lower(AuditLog.action).like(term)
            | func.lower(func.coalesce(AuditLog.resource_type, "")).like(term)
            | func.lower(func.coalesce(AuditLog.resource_id, "")).like(term)
            | func.lower(func.coalesce(AuditLog.request_id, "")).like(term)
            | func.lower(func.coalesce(User.display_name, "")).like(term)
        )
    if actor_user_id:
        filters.append(AuditLog.actor_user_id == actor_user_id)
    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if status:
        filters.append(AuditLog.status == status)
    if date_from:
        filters.append(AuditLog.created_at >= date_from)
    if date_to:
        filters.append(AuditLog.created_at <= date_to)
    total = (
        db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .where(*filters)
        )
        or 0
    )
    rows = db.execute(
        select(AuditLog, User.display_name)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .where(*filters)
        .order_by(desc(AuditLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": _safe_int(total),
        "items": [_audit_response(event, actor_name) for event, actor_name in rows],
    }
