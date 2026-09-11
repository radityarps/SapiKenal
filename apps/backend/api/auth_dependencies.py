"""FastAPI dependencies for session authentication and admin RBAC."""

from dataclasses import dataclass

from fastapi import Depends, Request  # pyright: ignore[reportMissingImports]
from fastapi.security import (  # pyright: ignore[reportMissingImports]
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from api.auth_security import authenticate_session
from api.errors import AdminAPIError
from db.core import get_db
from db.models import AuthSession, User

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedSession:
    user: User
    session: AuthSession
    token: str


def get_current_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> AuthenticatedSession:
    token = credentials.credentials if credentials else None
    authenticated = authenticate_session(db, token)
    if authenticated is None:
        raise AdminAPIError(401, "AUTH_REQUIRED", "Authentication is required")
    user, session = authenticated
    return AuthenticatedSession(user=user, session=session, token=token or "")


def require_admin(current: AuthenticatedSession = Depends(get_current_session)) -> User:
    if current.user.role != "admin":
        raise AdminAPIError(403, "ADMIN_REQUIRED", "Administrator access is required")
    return current.user
