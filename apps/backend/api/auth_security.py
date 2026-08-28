"""Password and opaque session token primitives."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from config import settings
from db.models import AuthSession, User, utc_now
from sqlalchemy import select
from sqlalchemy.orm import Session

_password_hasher = PasswordHasher()

_COMMON_PASSWORDS = {
    "password",
    "password123",
    "admin123",
    "admin1234",
    "sapikenal",
    "sapikenal123",
    "qwerty123",
}


def validate_password(password: str) -> None:
    """Apply the minimum password policy used by login and the seeder."""
    if len(password) < settings.password_min_length:
        raise ValueError(
            f"Password must contain at least {settings.password_min_length} characters"
        )
    if password.casefold() in _COMMON_PASSWORDS:
        raise ValueError("Password is too common")


def hash_password(password: str, *, validate: bool = True) -> str:
    if validate:
        validate_password(password)
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(
    db: Session, user: User, *, user_agent: str | None, ip_hash: str | None
) -> tuple[str, AuthSession]:
    """Create a random opaque session token and store only its hash."""
    raw_token = secrets.token_urlsafe(48)
    session = AuthSession(
        user_id=user.id,
        token_hash=_hash_session_token(raw_token),
        expires_at=utc_now() + timedelta(days=settings.session_ttl_days),
        user_agent=user_agent[:512] if user_agent else None,
        ip_hash=ip_hash,
    )
    db.add(session)
    db.flush()
    return raw_token, session


def authenticate_session(
    db: Session, raw_token: str | None
) -> tuple[User, AuthSession] | None:
    """Resolve a bearer token and reject expired, revoked, or inactive sessions."""
    if not raw_token:
        return None
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _hash_session_token(raw_token)
        )
    )
    if session is None or session.revoked_at is not None:
        return None
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=utc_now().tzinfo)
    if expires_at <= utc_now():
        return None
    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        return None
    session.last_used_at = utc_now()
    db.commit()
    return user, session


def revoke_session(session: AuthSession, db: Session) -> None:
    session.revoked_at = utc_now()
    db.add(session)


def revoke_all_sessions(user_id: str, db: Session) -> int:
    sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)
        )
    ).all()
    now = utc_now()
    for session in sessions:
        session.revoked_at = now
    return len(sessions)
