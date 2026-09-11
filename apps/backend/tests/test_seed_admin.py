import json
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import scripts.seed_admin as seed_module
from api.auth_security import issue_session
from db.base import Base
from db.models import AuditLog, AuthSession, GuideArticle, GuideArticleRevision, User


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


def test_guide_article_seed_is_complete_and_does_not_overwrite_edits(
    seed_context: sessionmaker[Session],
) -> None:
    assert seed_module.seed_guide_articles() == 48
    assert seed_module.seed_guide_articles() == 0

    with seed_context() as db:
        articles = db.scalars(select(GuideArticle)).all()
        assert len(articles) == 48
        assert {article.locale for article in articles} == {"id-ID", "en-US"}
        expected = {
            "app_1",
            "app_2",
            "app_3",
            "aceh_1",
            "aceh_2",
            "bali_1",
            "bali_2",
            "bali_3",
            "bali_4",
            "brahman_1",
            "brahman_2",
            "brahman_3",
            "brahman_4",
            "brangus_1",
            "brangus_2",
            "brangus_3",
            "limusin_1",
            "limusin_2",
            "madura_1",
            "madura_2",
            "pasundan_1",
            "pasundan_2",
            "po_1",
            "po_2",
        }
        assert {article.article_key for article in articles} == expected
        first = db.scalar(
            select(GuideArticleRevision).where(
                GuideArticleRevision.title == "Profil Sapi Bali"
            )
        )
        assert first is not None
        first.title = "Edited by administrator"
        db.commit()

    assert seed_module.seed_guide_articles() == 0
    with seed_context() as db:
        assert (
            db.scalar(
                select(GuideArticleRevision.title).where(
                    GuideArticleRevision.title == "Edited by administrator"
                )
            )
            == "Edited by administrator"
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda items: items + [items[0]], "duplicates"),
        (lambda items: [{**items[0], "locale": "xx"}], "locale"),
        (lambda items: [{**items[0], "category": "unknown"}], "category"),
        (lambda items: [{**items[0], "article_key": "Unsafe Key"}], "article_key"),
        (lambda items: [{**items[0], "sources": ["file:///tmp/source"]}], "sources"),
        (
            lambda items: [
                {**items[0], "sources": [f"https://example.org/{'x' * 2_030}"]}
            ],
            "sources",
        ),
        (lambda items: [{"article_key": "missing-fields"}], "category"),
    ],
)
def test_guide_article_seed_rejects_invalid_items_without_partial_insert(
    seed_context: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutate,
    message: str,
) -> None:
    valid = json.loads(seed_module.GUIDE_ARTICLE_SEED_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "guide_articles_seed.json"
    path.write_text(json.dumps(mutate(valid)), encoding="utf-8")
    monkeypatch.setattr(seed_module, "GUIDE_ARTICLE_SEED_PATH", path)

    with pytest.raises(RuntimeError, match=message):
        seed_module.seed_guide_articles()
    with seed_context() as db:
        assert db.scalar(select(GuideArticle)) is None


def test_guide_article_seed_rejects_malformed_root(
    seed_context: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "guide_articles_seed.json"
    path.write_text('{"items": []}', encoding="utf-8")
    monkeypatch.setattr(seed_module, "GUIDE_ARTICLE_SEED_PATH", path)

    with pytest.raises(RuntimeError, match="root must be a list"):
        seed_module.seed_guide_articles()


def test_guide_article_seed_allows_empty_sources_as_unreviewed_draft(
    seed_context: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    valid = json.loads(seed_module.GUIDE_ARTICLE_SEED_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "guide_articles_seed.json"
    path.write_text(json.dumps([{**valid[0], "sources": []}]), encoding="utf-8")
    monkeypatch.setattr(seed_module, "GUIDE_ARTICLE_SEED_PATH", path)

    assert seed_module.seed_guide_articles() == 1
    with seed_context() as db:
        article = db.scalar(select(GuideArticle))
        revision = db.scalar(select(GuideArticleRevision))
        assert article is not None and article.status == "draft"
        assert revision is not None
        assert revision.sources == []
        assert revision.status == "draft"
        assert revision.content_reviewed is False


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


def test_seed_guide_articles_activate_flag_and_activate_helper(
    seed_context: sessionmaker[Session],
) -> None:
    assert seed_module.seed_guide_articles(activate=False) == 48
    with seed_context() as db:
        drafts = db.scalars(
            select(GuideArticle).where(GuideArticle.status == "draft")
        ).all()
        assert len(drafts) == 48

    activated = seed_module.activate_guide_articles()
    assert activated == 48

    with seed_context() as db:
        active_articles = db.scalars(
            select(GuideArticle).where(GuideArticle.status == "active")
        ).all()
        active_revs = db.scalars(
            select(GuideArticleRevision).where(GuideArticleRevision.status == "active")
        ).all()
        assert len(active_articles) == 48
        assert len(active_revs) == 48
        assert all(rev.content_reviewed for rev in active_revs)

