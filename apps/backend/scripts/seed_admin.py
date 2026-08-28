"""Create or explicitly rotate the first admin account.

Usage is documented in the repository PRD. Credentials are supplied through
ADMIN_EMAIL, ADMIN_PASSWORD, and ADMIN_NAME; no defaults are provided.
"""

from __future__ import annotations

import argparse
import os
import sys

from api.auth_security import hash_password, revoke_all_sessions, validate_password
from config import settings
from db.core import SessionLocal, engine
from db.models import User
from pydantic import EmailStr, TypeAdapter, ValidationError
from services.audit import record_audit
from sqlalchemy import inspect, select


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} must be provided through the environment")
    return value


def _admin_credentials(
    *, allow_weak_password: bool = False
) -> tuple[EmailStr, str, str]:
    try:
        email = TypeAdapter(EmailStr).validate_python(_required_env("ADMIN_EMAIL"))
    except ValidationError as exc:
        raise ValueError("ADMIN_EMAIL must be a valid email address") from exc
    password = _required_env("ADMIN_PASSWORD")
    display_name = _required_env("ADMIN_NAME")
    if allow_weak_password:
        if settings.fastapi_env != "development" or not settings.debug:
            raise ValueError(
                "--allow-weak-password is only available in development with DEBUG=true"
            )
    else:
        validate_password(password)
    return email, password, display_name


def seed_admin(
    *, rotate_password: bool = False, allow_weak_password: bool = False
) -> str:
    """Create an idempotent admin or rotate its password explicitly."""
    if not inspect(engine).has_table("users"):
        raise RuntimeError("Database migration has not been applied")

    email, password, display_name = _admin_credentials(
        allow_weak_password=allow_weak_password
    )

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            if user.role != "admin":
                raise RuntimeError(
                    "An existing user account cannot be taken over as admin"
                )
            if user.status != "active":
                raise RuntimeError("Existing admin account is not active")
            if not rotate_password:
                return "admin already exists; no changes made"
            user.password_hash = hash_password(
                password, validate=not allow_weak_password
            )
            user.must_change_password = False
            revoked_sessions = revoke_all_sessions(user.id, db)
            record_audit(
                db,
                action="seed_admin_password_rotated",
                actor_user_id=user.id,
                resource_type="user",
                resource_id=user.id,
                changed_fields={
                    "password": "changed",
                    "revoked_sessions": revoked_sessions,
                },
                reason="explicit --rotate-password",
            )
            db.commit()
            return "admin password rotated"

        user = User(
            email=email,
            password_hash=hash_password(password, validate=not allow_weak_password),
            display_name=display_name,
            role="admin",
            status="active",
        )
        db.add(user)
        db.flush()
        record_audit(
            db,
            action="seed_admin_created",
            actor_user_id=user.id,
            resource_type="user",
            resource_id=user.id,
            changed_fields={"email": "set", "role": "admin"},
            reason="one-shot admin seeder",
        )
        db.commit()
        return "admin created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the SapiKenal admin account")
    parser.add_argument("--rotate-password", action="store_true")
    parser.add_argument(
        "--allow-weak-password",
        action="store_true",
        help="Allow a weak password for an explicit local development bootstrap",
    )
    args = parser.parse_args(argv)
    try:
        print(
            seed_admin(
                rotate_password=args.rotate_password,
                allow_weak_password=args.allow_weak_password,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"seed-admin failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
