"""Authentication endpoints for the admin BFF and future mobile auth."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from db.core import get_db
from db.models import User
from fastapi import APIRouter, Depends, Request
from services.audit import record_audit
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.auth_dependencies import AuthenticatedSession, get_current_session
from api.auth_schemas import (
    AuthUser,
    ChangePasswordRequest,
    LoginRequest,
    MeResponse,
    MessageResponse,
    SessionResponse,
)
from api.auth_security import (
    hash_password,
    issue_session,
    revoke_all_sessions,
    revoke_session,
    verify_password,
)
from api.errors import AdminAPIError

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _ip_hash(request: Request) -> str | None:
    client = request.client.host if request.client else None
    if not client:
        return None
    return hashlib.sha256(client.encode("utf-8")).hexdigest()


def _public_user(user: User) -> AuthUser:
    return AuthUser.model_validate(user)


def _invalid_login(db: Session, request: Request, reason: str) -> None:
    record_audit(
        db,
        action="login_failed",
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        status="failed",
        reason=reason,
    )
    db.commit()


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email).strip().casefold()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        _invalid_login(db, request, "invalid_credentials")
        raise AdminAPIError(
            401, "AUTH_INVALID_CREDENTIALS", "Email atau kata sandi tidak valid"
        )

    if user.status != "active":
        _invalid_login(db, request, "inactive_account")
        raise AdminAPIError(403, "ACCOUNT_INACTIVE", "Akun tidak aktif")
    if user.role != "admin":
        _invalid_login(db, request, "non_admin_role")
        raise AdminAPIError(403, "ADMIN_REQUIRED", "Administrator access is required")

    raw_token, session = issue_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_hash=_ip_hash(request),
    )
    user.last_login_at = datetime.now(timezone.utc)
    record_audit(
        db,
        action="login_succeeded",
        actor_user_id=user.id,
        resource_type="auth_session",
        resource_id=session.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return SessionResponse(
        session_token=raw_token,
        expires_at=session.expires_at,
        user=_public_user(user),
    )


@router.post("/refresh", response_model=SessionResponse)
def refresh(
    request: Request,
    current: AuthenticatedSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    revoke_session(current.session, db)
    raw_token, session = issue_session(
        db,
        current.user,
        user_agent=request.headers.get("user-agent"),
        ip_hash=_ip_hash(request),
    )
    record_audit(
        db,
        action="session_refreshed",
        actor_user_id=current.user.id,
        resource_type="auth_session",
        resource_id=session.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return SessionResponse(
        session_token=raw_token,
        expires_at=session.expires_at,
        user=_public_user(current.user),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    current: AuthenticatedSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    revoke_session(current.session, db)
    record_audit(
        db,
        action="logout",
        actor_user_id=current.user.id,
        resource_type="auth_session",
        resource_id=current.session.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
    )
    db.commit()
    return {"status": "success", "message": "Session revoked"}


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    request: Request,
    current: AuthenticatedSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    revoked_count = revoke_all_sessions(current.user.id, db)
    record_audit(
        db,
        action="logout_all",
        actor_user_id=current.user.id,
        resource_type="user",
        resource_id=current.user.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"revoked_sessions": revoked_count},
    )
    db.commit()
    return {"status": "success", "message": "All sessions revoked"}


@router.get("/me", response_model=MeResponse)
def me(current: AuthenticatedSession = Depends(get_current_session)):
    return {"status": "success", "user": _public_user(current.user)}


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current: AuthenticatedSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current.user.password_hash):
        raise AdminAPIError(
            400, "CURRENT_PASSWORD_INVALID", "Current password is invalid"
        )
    try:
        new_hash = hash_password(payload.new_password)
    except ValueError as exc:
        raise AdminAPIError(422, "WEAK_PASSWORD", str(exc)) from exc

    current.user.password_hash = new_hash
    current.user.must_change_password = False
    revoke_all_sessions(current.user.id, db)
    record_audit(
        db,
        action="password_changed",
        actor_user_id=current.user.id,
        resource_type="user",
        resource_id=current.user.id,
        request_id=_request_id(request),
        ip_hash=_ip_hash(request),
        changed_fields={"password": "changed", "sessions": "revoked"},
    )
    db.commit()
    return {"status": "success", "message": "Password changed; sign in again"}
