from collections.abc import Generator

import pytest
import scripts.seed_admin as seed_module
from api.auth_security import issue_session
from db.base import Base
from db.models import AuditLog, AuthSession, User
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def seed_context(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(seed_module, "engine", engine)
    monkeypatch.setattr(seed_module, "SessionLocal", session_factory)
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "A-strong-admin-password")
    monkeypatch.setenv("ADMIN_NAME", "Administrator")
    yield session_factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_seed_is_idempotent(seed_context: sessionmaker[Session]) -> None:
    assert seed_module.seed_admin() == "admin created"
    assert seed_module.seed_admin() == "admin already exists; no changes made"

    with seed_context() as db:
        assert (
            db.scalar(select(User).where(User.email == "admin@example.com")) is not None
        )
        assert (
            db.scalar(select(AuditLog).where(AuditLog.action == "seed_admin_created"))
            is not None
        )


def test_seed_rejects_weak_password(
    seed_context: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "password123")
    with pytest.raises(ValueError):
        seed_module.seed_admin()


def test_dev_seed_allows_weak_password_only_when_explicit(
    seed_context: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(seed_module.settings, "fastapi_env", "development")
    monkeypatch.setattr(seed_module.settings, "debug", True)
    monkeypatch.setattr(seed_module.settings, "password_min_length", 12)
    monkeypatch.setenv("ADMIN_PASSWORD", "short")

    assert seed_module.seed_admin(allow_weak_password=True) == "admin created"


def test_seed_does_not_take_over_user(seed_context: sessionmaker[Session]) -> None:
    with seed_context() as db:
        from api.auth_security import hash_password

        db.add(
            User(
                email="admin@example.com",
                password_hash=hash_password("A-strong-user-password"),
                display_name="Existing User",
                role="user",
                status="active",
            )
        )
        db.commit()

    with pytest.raises(RuntimeError, match="cannot be taken over"):
        seed_module.seed_admin()


def test_explicit_rotation_revokes_existing_sessions(
    seed_context: sessionmaker[Session],
) -> None:
    seed_module.seed_admin()
    with seed_context() as db:
        user = db.scalar(select(User).where(User.email == "admin@example.com"))
        assert user is not None
        _, session = issue_session(
            db,
            user,
            user_agent="test",
            ip_hash=None,
        )
        db.commit()
        session_id = session.id

    assert seed_module.seed_admin(rotate_password=True) == "admin password rotated"
    with seed_context() as db:
        refreshed = db.get(AuthSession, session_id)
        assert refreshed is not None
        assert refreshed.revoked_at is not None
        assert (
            db.scalar(
                select(AuditLog).where(AuditLog.action == "seed_admin_password_rotated")
            )
            is not None
        )
