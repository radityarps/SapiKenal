from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.auth_security import hash_password, issue_session
from db.base import Base
from db.core import get_db
from db.models import AuditLog, GuideArticleRevision, User
from main import app


@pytest.fixture()
def article_client() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as db:
        admin = User(
            email="article-admin@example.com",
            password_hash=hash_password("A-strong-admin-password"),
            display_name="Article Admin",
            role="admin",
            status="active",
        )
        db.add(admin)
        db.flush()
        token, _ = issue_session(db, admin, user_agent="test", ip_hash=None)
        db.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        client.headers.update({"Authorization": f"Bearer {token}"})
        yield client, session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "article_key": "profil-bali",
        "locale": "id-ID",
        "category": "bali",
        "sort_order": 10,
        "title": "Profil Sapi Bali",
        "summary": "Ringkasan profil sapi Bali.",
        "body": "Informasi tentang karakteristik sapi Bali.",
        "sources": ["https://example.com/bali"],
    }
    payload.update(overrides)
    return payload


def test_article_lifecycle_and_deterministic_locale_snapshot(
    article_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = article_client
    created = client.post("/api/admin/articles", json=_payload())
    assert created.status_code == 201
    article_id = created.json()["item"]["id"]

    assert client.get("/api/content/articles?locale=id-ID").json() == {
        "status": "success",
        "locale": "id-ID",
        "snapshot_version": client.get("/api/content/articles?locale=id-ID").json()[
            "snapshot_version"
        ],
        "items": [],
    }
    assert client.post(f"/api/admin/articles/{article_id}/review").status_code == 200
    assert client.post(f"/api/admin/articles/{article_id}/activate").status_code == 200

    first = client.get("/api/content/articles", params={"locale": "id-ID"})
    second = client.get("/api/content/articles", params={"locale": "id-ID"})
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.json()["locale"] == "id-ID"
    assert first.json()["items"] == [
        {
            "article_key": "profil-bali",
            "category": "bali",
            "sort_order": 10,
            "title": "Profil Sapi Bali",
            "summary": "Ringkasan profil sapi Bali.",
            "body": "Informasi tentang karakteristik sapi Bali.",
            "sources": ["https://example.com/bali"],
            "revision": 1,
        }
    ]

    with session_factory() as db:
        actions = db.scalars(
            select(AuditLog.action).order_by(AuditLog.created_at, AuditLog.id)
        ).all()
    assert actions == ["article_created", "article_reviewed", "article_activated"]

    assert (
        client.post(f"/api/admin/articles/{article_id}/deactivate").status_code == 200
    )
    assert client.get("/api/content/articles?locale=id-ID").json()["items"] == []


def test_article_revision_preserves_public_version_until_activation(
    article_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, session_factory = article_client
    created = client.post("/api/admin/articles", json=_payload())
    article_id = created.json()["item"]["id"]
    assert client.post(f"/api/admin/articles/{article_id}/review").status_code == 200
    assert client.post(f"/api/admin/articles/{article_id}/activate").status_code == 200

    revised = client.post(
        f"/api/admin/articles/{article_id}/revise",
        json={"body": "Revisi konten."},
    )
    assert revised.status_code == 200
    assert revised.json()["item"]["publication_status"] == "active"
    assert revised.json()["item"]["revision"]["status"] == "draft"
    assert revised.json()["item"]["revision"]["content_reviewed"] is False
    assert revised.json()["item"]["active_revision"]["revision"] == 1
    assert (
        client.get("/api/content/articles?locale=id-ID").json()["items"][0]["body"]
        == "Informasi tentang karakteristik sapi Bali."
    )

    draft = client.get(
        "/api/admin/articles",
        params={"category": "bali", "locale": "id-ID", "revision_status": "draft"},
    )
    assert draft.status_code == 200
    assert draft.json()["total"] == 1
    assert draft.json()["items"][0]["publication_status"] == "active"
    assert draft.json()["items"][0]["revision"]["status"] == "draft"
    assert draft.json()["items"][0]["active_revision"]["revision"] == 1

    published = client.get(
        "/api/admin/articles",
        params={"publication_status": "active", "page": 1, "page_size": 1},
    )
    assert published.status_code == 200
    assert published.json()["total"] == 1
    assert published.json()["items"][0]["article_key"] == "profil-bali"

    assert client.post(f"/api/admin/articles/{article_id}/review").status_code == 200
    assert client.post(f"/api/admin/articles/{article_id}/activate").status_code == 200
    snapshot = client.get("/api/content/articles?locale=id-ID").json()["items"]
    assert snapshot[0]["body"] == "Revisi konten."
    assert snapshot[0]["revision"] == 2
    with session_factory() as db:
        assert (
            len(
                db.scalars(
                    select(GuideArticleRevision).where(
                        GuideArticleRevision.article_id == article_id,
                        GuideArticleRevision.status == "active",
                    )
                ).all()
            )
            == 1
        )
    assert (
        client.post(f"/api/admin/articles/{article_id}/deactivate").status_code == 200
    )
    assert client.get("/api/content/articles?locale=id-ID").json()["items"] == []


def test_article_listing_paginates_after_database_filters(
    article_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = article_client
    for index, (key, category) in enumerate(
        [("app_2", "app_usage"), ("bali_2", "bali"), ("bali_3", "bali")]
    ):
        response = client.post(
            "/api/admin/articles",
            json=_payload(
                article_key=key,
                category=category,
                title=f"Artikel {index}",
            ),
        )
        assert response.status_code == 201

    first = client.get(
        "/api/admin/articles",
        params={"category": "bali", "page": 1, "page_size": 1},
    ).json()
    second = client.get(
        "/api/admin/articles",
        params={"category": "bali", "page": 2, "page_size": 1},
    ).json()
    assert first["total"] == 2
    assert second["total"] == 2
    assert first["items"][0]["article_key"] == "bali_2"
    assert second["items"][0]["article_key"] == "bali_3"


def test_locale_pair_metadata_ignores_current_filter(
    article_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = article_client
    indonesia = client.post("/api/admin/articles", json=_payload()).json()["item"]
    english = client.post(
        "/api/admin/articles",
        json=_payload(locale="en-US", title="Bali Cattle Profile"),
    ).json()["item"]
    assert client.post(f"/api/admin/articles/{english['id']}/review").status_code == 200
    assert (
        client.post(f"/api/admin/articles/{english['id']}/activate").status_code == 200
    )

    filtered = client.get("/api/admin/articles", params={"locale": "id-ID"}).json()
    assert filtered["items"][0]["id"] == indonesia["id"]
    assert filtered["items"][0]["locale_pair"] == {
        "locale": "en-US",
        "status": "active",
    }


def test_article_boundary_validation_and_stable_identity(
    article_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, _ = article_client
    assert (
        client.post(
            "/api/admin/articles", json=_payload(sources=["javascript:alert(1)"])
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/articles", json=_payload(category="unknown")
        ).status_code
        == 422
    )
    assert (
        client.post("/api/admin/articles", json=_payload(body="x" * 50_001)).status_code
        == 422
    )

    created = client.post("/api/admin/articles", json=_payload()).json()
    article_id = created["item"]["id"]
    changed_key = client.patch(
        f"/api/admin/articles/{article_id}", json={"article_key": "different"}
    )
    assert changed_key.status_code == 422
    assert changed_key.json()["code"] == "ARTICLE_IDENTITY_IMMUTABLE"

    assert client.get("/api/content/articles?locale=fr-FR").status_code == 422
    assert (
        client.get("/api/admin/articles", params={"category": "unknown"}).status_code
        == 422
    )
