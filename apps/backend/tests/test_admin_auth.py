from collections.abc import Generator

import pytest
from api.auth_security import hash_password
from db.base import Base
from db.core import get_db
from db.models import User
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as db:
        db.add_all(
            [
                User(
                    email="admin@example.com",
                    password_hash=hash_password("A-strong-admin-password"),
                    display_name="Test Admin",
                    role="admin",
                    status="active",
                ),
                User(
                    email="user@example.com",
                    password_hash=hash_password("A-strong-user-password"),
                    display_name="Test User",
                    role="user",
                    status="active",
                ),
            ]
        )
        db.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_admin_can_login_use_session_and_logout(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"email": "ADMIN@example.com", "password": "A-strong-admin-password"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["user"]["role"] == "admin"
    assert body["session_token"]

    token = body["session_token"]
    assert (
        client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )
    access = client.get(
        "/api/admin/access", headers={"Authorization": f"Bearer {token}"}
    )
    assert access.status_code == 200
    assert access.json()["user"]["email"] == "admin@example.com"

    assert (
        client.post(
            "/api/auth/logout", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 200
    )
    revoked = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked.status_code == 401
    assert revoked.json()["code"] == "AUTH_REQUIRED"


def test_user_role_is_rejected_from_admin_login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "A-strong-user-password"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "ADMIN_REQUIRED"


def test_invalid_login_is_generic(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_INVALID_CREDENTIALS"
    assert "not found" not in response.json()["message"].lower()
