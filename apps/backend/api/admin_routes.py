# ruff: noqa: B008
"""Protected admin MVP routes for operations, users, content, and models."""

from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Literal, cast

from fastapi import (  # pyright: ignore[reportMissingImports]
    APIRouter,
    Depends,
    Query,
    Request,
)
from sqlalchemy import (  # pyright: ignore[reportMissingImports]
    asc,
    desc,
    func,
    or_,
    select,
)
from sqlalchemy.exc import IntegrityError  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session, aliased  # pyright: ignore[reportMissingImports]

from config import CANONICAL_LABELS, settings
from db.core import get_db
from db.models import (
    AuditLog,
    DetectionHistory,
    GuideArticle,
    GuideArticleRevision,
    PredictionEvent,
    User,
)
from inference_server import get_model_status
from services.audit import mask_device_id, period_start, record_audit

from .admin_schemas import (  # pyright: ignore[reportMissingImports]
    AuditLogResponse,
    GuideArticlePatchRequest,
    GuideArticleRequest,
    GuideArticleResponse,
    GuideArticleRevisionResponse,
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
_ALLOWED_ARTICLE_CATEGORIES = {
    "app_usage",
    "aceh",
    "bali",
    "brahman",
    "brangus",
    "limusin",
    "madura",
    "pasundan",
    "po",
}


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
        "aceh": "Aceh",
        "bali": "Bali",
        "limusin": "Limusin",
        "madura": "Madura",
        "non_sapi": "Bukan Sapi",
        "pasundan": "Pasundan",
        "po": "PO",
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
    if (
        inference_mode
        and item["inference_mode"].casefold() != inference_mode.casefold()
    ):
        return False
    return not model_version or item["model_version"] == model_version


def _latest_article_revision(
    db: Session, article_id: str
) -> GuideArticleRevision | None:
    return db.scalar(
        select(GuideArticleRevision)
        .where(GuideArticleRevision.article_id == article_id)
        .order_by(desc(GuideArticleRevision.revision))
    )


def _active_article_revision(
    db: Session, article_id: str
) -> GuideArticleRevision | None:
    return db.scalar(
        select(GuideArticleRevision).where(
            GuideArticleRevision.article_id == article_id,
            GuideArticleRevision.status == "active",
        )
    )


def _article_response(
    article: GuideArticle,
    revision: GuideArticleRevision,
    active_revision: GuideArticleRevision | None = None,
) -> dict[str, Any]:
    return GuideArticleResponse(
        id=article.id,
        article_key=article.article_key,
        publication_status=cast(Literal["draft", "active", "inactive"], article.status),
        revision=GuideArticleRevisionResponse.model_validate(revision),
        active_revision=(
            GuideArticleRevisionResponse.model_validate(active_revision)
            if active_revision is not None
            else None
        ),
        created_at=article.created_at,
        updated_at=article.updated_at,
    ).model_dump(mode="json")


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
    average_confidence = (
        sum(item["confidence"] for item in accepted_items) / accepted
        if accepted
        else None
    )
    timings = [
        _safe_int(item["processing_ms"])
        for item in prediction_items
        if item["processing_ms"] is not None
    ]
    timings.sort()
    p95 = timings[max(0, math.ceil(len(timings) * 0.95) - 1)] if timings else None
    attempts = accepted + failures
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
            "average_confidence": average_confidence,
            "failures": _safe_int(failures),
            "median_processing_ms": median(timings) if timings else None,
            "p95_processing_ms": p95,
        },
        "model": {
            "version": health.get("model_version", settings.model_version),
            "activated_at": None,
            "status": "active" if health["model_loaded"] else "degraded",
        },
        "health": {
            "status": "ok" if health["model_loaded"] else "degraded",
            "model_loaded": health["model_loaded"],
            "model_version": health.get("model_version", settings.model_version),
            "desired_model_version": settings.model_version,
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
    predicted_class: Literal[
        "aceh", "bali", "limusin", "madura", "non_sapi", "pasundan", "po"
    ]
    | None = None,
    status: Literal["success", "failed"] | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=1),
    max_confidence: float | None = Query(default=None, ge=0, le=1),
    inference_mode: Literal["online", "offline", "offline_fallback", "unknown"]
    | None = None,
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


@router.get("/articles")
def list_articles(
    category: Literal[
        "app_usage",
        "aceh",
        "bali",
        "brahman",
        "brangus",
        "limusin",
        "madura",
        "pasundan",
        "po",
    ]
    | None = None,
    publication_status: Literal["draft", "active", "inactive"] | None = None,
    revision_status: Literal["draft", "active", "inactive"] | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=_PAGE_SIZE_MAX),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    page, page_size = _page(page, page_size)
    latest_number = (
        select(
            GuideArticleRevision.article_id,
            func.max(GuideArticleRevision.revision).label("revision"),
        )
        .group_by(GuideArticleRevision.article_id)
        .subquery()
    )
    latest = aliased(GuideArticleRevision)
    active = aliased(GuideArticleRevision)
    filters = []
    if publication_status:
        filters.append(GuideArticle.status == publication_status)
    if category:
        filters.append(latest.category == category)
    if revision_status:
        filters.append(latest.status == revision_status)
    query = (
        select(GuideArticle, latest, active)
        .join(latest_number, latest_number.c.article_id == GuideArticle.id)
        .join(
            latest,
            (latest.article_id == latest_number.c.article_id)
            & (latest.revision == latest_number.c.revision),
        )
        .outerjoin(
            active,
            (active.article_id == GuideArticle.id) & (active.status == "active"),
        )
        .where(*filters)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    # SQLAlchemy statement is built only from typed, allowlisted filters above.
    # pi-lens-ignore: python-sql-injection
    rows = db.execute(
        query.order_by(asc(GuideArticle.article_key))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        _article_response(article, revision, active_revision)
        for article, revision, active_revision in rows
    ]
    return {
        "status": "success",
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items,
    }


@router.post("/articles", status_code=201)
def create_article(
    payload: GuideArticleRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.scalar(
        select(GuideArticle).where(
            GuideArticle.article_key == payload.article_key,
        )
    )
    if existing is not None:
        raise AdminAPIError(409, "ARTICLE_EXISTS", "Guide article already exists")
    article = GuideArticle(
        article_key=payload.article_key,
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(article)
    db.flush()
    revision = GuideArticleRevision(
        article_id=article.id,
        revision=1,
        category=payload.category,
        sort_order=payload.sort_order,
        title=payload.title,
        summary=payload.summary,
        body=payload.body,
        sources=payload.sources,
        content_reviewed=False,
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
    )
    db.add(revision)
    record_audit(
        db,
        action="article_created",
        actor_user_id=admin.id,
        resource_type="guide_article",
        resource_id=article.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"article_key": "set", "revision": 1},
    )
    db.commit()
    return {"status": "success", "item": _article_response(article, revision)}


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    article = db.get(GuideArticle, article_id)
    revision = _latest_article_revision(db, article_id) if article else None
    if article is None or revision is None:
        raise AdminAPIError(404, "ARTICLE_NOT_FOUND", "Guide article not found")
    return {
        "status": "success",
        "item": _article_response(
            article, revision, _active_article_revision(db, article.id)
        ),
    }


@router.post("/articles/{article_id}/revise")
def revise_article(
    article_id: str,
    payload: GuideArticlePatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = db.get(GuideArticle, article_id)
    current = _latest_article_revision(db, article_id) if article else None
    if article is None or current is None:
        raise AdminAPIError(404, "ARTICLE_NOT_FOUND", "Guide article not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise AdminAPIError(422, "NO_CHANGES", "At least one field must be changed")
    if "article_key" in changes:
        raise AdminAPIError(
            422,
            "ARTICLE_IDENTITY_IMMUTABLE",
            "Article key cannot be changed",
        )
    if "content_reviewed" in changes:
        raise AdminAPIError(
            422,
            "ARTICLE_REVIEW_INVALID",
            "Review saved article content separately from content changes",
        )
    values = {
        "category": current.category,
        "sort_order": current.sort_order,
        "title": current.title,
        "summary": current.summary,
        "body": current.body,
        "sources": current.sources,
    }
    values.update(changes)
    revision = GuideArticleRevision(
        article_id=article.id,
        revision=current.revision + 1,
        content_reviewed=False,
        status="draft",
        created_by=admin.id,
        updated_by=admin.id,
        **values,
    )
    db.add(revision)
    # GuideArticle.status is publication state. Keep it active while the new
    # editorial revision remains a draft; revision.status represents that draft.
    article.updated_by = admin.id
    record_audit(
        db,
        action="article_revised",
        actor_user_id=admin.id,
        resource_type="guide_article",
        resource_id=article.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields=dict.fromkeys(changes, "changed"),
    )
    db.commit()
    return {
        "status": "success",
        "item": _article_response(
            article, revision, _active_article_revision(db, article.id)
        ),
    }


@router.patch("/articles/{article_id}")
def patch_article(
    article_id: str,
    payload: GuideArticlePatchRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    changes = payload.model_dump(exclude_unset=True)
    if "article_key" in changes:
        raise AdminAPIError(
            422,
            "ARTICLE_IDENTITY_IMMUTABLE",
            "Article key cannot be changed",
        )
    if changes == {"content_reviewed": True}:
        return review_article(article_id, request, db, admin)
    return revise_article(article_id, payload, request, db, admin)


@router.post("/articles/{article_id}/review")
def review_article(
    article_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = db.get(GuideArticle, article_id)
    revision = _latest_article_revision(db, article_id) if article else None
    if article is None or revision is None:
        raise AdminAPIError(404, "ARTICLE_NOT_FOUND", "Guide article not found")
    if revision.content_reviewed:
        raise AdminAPIError(
            409, "ARTICLE_ALREADY_REVIEWED", "Article is already reviewed"
        )
    revision.content_reviewed = True
    revision.updated_by = admin.id
    article.updated_by = admin.id
    record_audit(
        db,
        action="article_reviewed",
        actor_user_id=admin.id,
        resource_type="guide_article",
        resource_id=article.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"content_reviewed": True, "revision": revision.revision},
    )
    db.commit()
    return {
        "status": "success",
        "item": _article_response(
            article, revision, _active_article_revision(db, article.id)
        ),
    }


@router.post("/articles/{article_id}/activate")
def activate_article(
    article_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = db.get(GuideArticle, article_id)
    revision = _latest_article_revision(db, article_id) if article else None
    if article is None or revision is None:
        raise AdminAPIError(404, "ARTICLE_NOT_FOUND", "Guide article not found")
    if not revision.content_reviewed or not revision.sources:
        raise AdminAPIError(
            422,
            "ARTICLE_REVIEW_REQUIRED",
            "Article content and sources must be reviewed before activation",
        )
    for previous in db.scalars(
        select(GuideArticleRevision).where(
            GuideArticleRevision.article_id == article.id,
            GuideArticleRevision.status == "active",
        )
    ).all():
        previous.status = "inactive"
    db.flush()
    revision.status = "active"
    article.status = "active"
    article.updated_by = admin.id
    record_audit(
        db,
        action="article_activated",
        actor_user_id=admin.id,
        resource_type="guide_article",
        resource_id=article.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"status": "active", "revision": revision.revision},
    )
    db.commit()
    return {
        "status": "success",
        "item": _article_response(article, revision, revision),
    }


@router.post("/articles/{article_id}/deactivate")
def deactivate_article(
    article_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    article = db.get(GuideArticle, article_id)
    revision = _latest_article_revision(db, article_id) if article else None
    if article is None or revision is None:
        raise AdminAPIError(404, "ARTICLE_NOT_FOUND", "Guide article not found")
    for active in db.scalars(
        select(GuideArticleRevision).where(
            GuideArticleRevision.article_id == article.id,
            GuideArticleRevision.status == "active",
        )
    ).all():
        active.status = "inactive"
    article.status = "inactive"
    article.updated_by = admin.id
    record_audit(
        db,
        action="article_deactivated",
        actor_user_id=admin.id,
        resource_type="guide_article",
        resource_id=article.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"status": "inactive"},
    )
    db.commit()
    return {
        "status": "success",
        "item": _article_response(
            article, revision, _active_article_revision(db, article.id)
        ),
    }


@content_router.get("/articles")
def public_articles(
    locale: str | None = None,
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(GuideArticle, GuideArticleRevision)
        .join(
            GuideArticleRevision,
            GuideArticleRevision.article_id == GuideArticle.id,
        )
        .where(
            GuideArticleRevision.status == "active",
        )
        .order_by(
            asc(GuideArticleRevision.category),
            asc(GuideArticleRevision.sort_order),
            asc(GuideArticle.article_key),
        )
    ).all()
    items = [
        {
            "article_key": article.article_key,
            "category": revision.category,
            "sort_order": revision.sort_order,
            "title": revision.title,
            "summary": revision.summary,
            "body": revision.body,
            "sources": revision.sources,
            "revision": revision.revision,
        }
        for article, revision in rows
    ]
    canonical = json.dumps(
        items, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return {
        "status": "success",
        "locale": locale or "id-ID",
        "snapshot_version": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "items": items,
    }


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
