from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.exc import IntegrityError

from alembic import command

BACKEND = Path(__file__).parents[1]


def _config(path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    from config import settings

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{path}")
    config = Config(BACKEND / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return config


def _insert_profile(
    engine: sa.Engine, *, key: str = "bali", locale: str = "id-ID"
) -> None:
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        # Static test SQL; all variable values use bound parameters.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text(
                "INSERT INTO breed_profiles "
                "(id, canonical_key, locale, status, created_at, updated_at) "
                "VALUES ('profile-1', :key, :locale, 'draft', :now, :now)"
            ),
            {"key": key, "locale": locale, "now": now},
        )
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text(
                "INSERT INTO breed_profile_revisions "
                "(id, profile_id, revision, display_name, summary, strengths, "
                "limitations, disclaimer, status, created_at, updated_at, sources, content_reviewed) "
                "VALUES ('revision-1', 'profile-1', 3, 'Profil Bali', 'Ringkasan', "
                "'Kuat', 'Terbatas', 'Bukan bukti silsilah', 'draft', :now, :now, "
                "'[\"https://example.org/bali\"]', 1)"
            ),
            {"now": now},
        )


def test_upgrade_0008_to_0009_preserves_profile_and_enforces_invariants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "migration.sqlite3"
    config = _config(path, monkeypatch)
    command.upgrade(config, "0008_breed_profile_review")
    engine = sa.create_engine(f"sqlite:///{path}")
    _insert_profile(engine)

    command.upgrade(config, "0009_article_cms")

    inspector = sa.inspect(engine)
    assert "guide_articles" in inspector.get_table_names()
    assert "breed_profiles" not in inspector.get_table_names()
    assert {
        item["name"] for item in inspector.get_indexes("guide_article_revisions")
    } >= {
        "ix_guide_article_revisions_article_id",
        "uq_guide_article_revisions_one_active",
    }
    with engine.connect() as connection:
        # Static inspection query with no external input.
        # pi-lens-ignore: python-sql-injection
        row = (
            connection.execute(
                sa.text(
                    "SELECT a.article_key, a.locale, r.category, r.title, r.summary, r.body, "
                    "r.sources, r.content_reviewed, r.status, r.revision "
                    "FROM guide_articles a JOIN guide_article_revisions r ON r.article_id = a.id"
                )
            )
            .mappings()
            .one()
        )
        assert row["article_key"] == "bali_1"
        assert row["locale"] == "id-ID"
        assert row["category"] == "bali"
        assert row["title"] == "Profil Bali"
        assert row["summary"] == "Ringkasan"
        assert "Kuat" in row["body"] and "Terbatas" in row["body"]
        assert row["sources"] == '["https://example.org/bali"]'
        assert row["content_reviewed"] == 1
        assert row["status"] == "draft"
        assert row["revision"] == 3

    article_id = "profile-1"
    with engine.connect() as connection:
        # SQLite test setup uses fixed PRAGMA statements with no external input.
        # pi-lens-ignore: python-sql-injection
        connection.execute(sa.text("PRAGMA foreign_keys=ON"))
        # pi-lens-ignore: python-sql-injection
        assert connection.execute(sa.text("PRAGMA foreign_keys")).scalar_one() == 1
    invalid_statements = [
        ("UPDATE guide_articles SET locale='xx' WHERE id=:id", {}),
        ("UPDATE guide_articles SET status='xx' WHERE id=:id", {}),
        ("UPDATE guide_article_revisions SET category='xx' WHERE article_id=:id", {}),
        ("UPDATE guide_article_revisions SET status='xx' WHERE article_id=:id", {}),
        (
            "INSERT INTO guide_articles "
            "(id, article_key, locale, status, created_at, updated_at) VALUES "
            "('duplicate-article', 'bali_1', 'id-ID', 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            {},
        ),
        (
            "INSERT INTO guide_article_revisions "
            "(id, article_id, revision, category, icon, sort_order, title, summary, body, "
            "sources, content_reviewed, status, created_at, updated_at) VALUES "
            "('duplicate-revision', :id, 3, 'bali', 'x', 10, 'x', 'x', 'x', '[]', 0, "
            "'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            {},
        ),
        (
            "INSERT INTO guide_article_revisions "
            "(id, article_id, revision, category, icon, sort_order, title, summary, body, "
            "sources, content_reviewed, status, created_at, updated_at) VALUES "
            "('orphan-revision', 'missing-article', 1, 'bali', 'x', 10, 'x', 'x', 'x', "
            "'[]', 0, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            {},
        ),
    ]
    for statement, values in invalid_statements:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            # Statements are fixed allowlisted test cases; values are bound.
            # pi-lens-ignore: python-sql-injection
            connection.execute(sa.text(statement), {"id": article_id, **values})

    with engine.begin() as connection:
        # Static test setup query with no external input.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text(
                "UPDATE guide_article_revisions SET status='active' WHERE id='revision-1'"
            )
        )
    with pytest.raises(IntegrityError), engine.begin() as connection:
        # Static test query; article_id uses a bound parameter.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text(
                "INSERT INTO guide_article_revisions "
                "(id, article_id, revision, category, icon, sort_order, title, summary, body, "
                "sources, content_reviewed, status, created_at, updated_at) VALUES "
                "('revision-2', :id, 4, 'bali', 'x', 10, 'x', 'x', 'x', '[]', 0, "
                "'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": article_id},
        )


def test_upgrade_0009_fails_clearly_for_unsupported_source_data(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "article_cms_migration", BACKEND / "alembic/versions/0009_article_cms.py"
    )
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    sa.Table(
        "breed_profiles",
        metadata,
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("canonical_key", sa.String),
        sa.Column("locale", sa.String),
        sa.Column("status", sa.String),
    )
    sa.Table(
        "breed_profile_revisions",
        metadata,
        sa.Column("profile_id", sa.String),
        sa.Column("revision", sa.Integer),
        sa.Column("status", sa.String),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        # Static migration-fixture queries with no external input.
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text(
                "INSERT INTO breed_profiles VALUES ('1', 'unsupported', 'id-ID', 'draft')"
            )
        )
        with pytest.raises(RuntimeError, match="unsupported guide article key"):
            migration._validate_source_data(connection)
        # pi-lens-ignore: python-sql-injection
        connection.execute(sa.text("DELETE FROM breed_profiles"))
        # pi-lens-ignore: python-sql-injection
        connection.execute(
            sa.text("INSERT INTO breed_profiles VALUES ('1', 'bali', 'xx', 'draft')")
        )
        with pytest.raises(RuntimeError, match="unsupported guide article locale"):
            migration._validate_source_data(connection)


def test_migration_0011_removes_icon_column(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "test_migration_0011.db"
    config = _config(db_path, monkeypatch)
    command.upgrade(config, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("guide_article_revisions")}
    assert "icon" not in columns
    assert "category" in columns
    assert "title" in columns
    assert "body" in columns


def test_migration_0012_removes_location_columns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "test_migration_0012.db"
    config = _config(db_path, monkeypatch)
    command.upgrade(config, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("detection_history")}
    assert "latitude" not in columns
    assert "longitude" not in columns
    assert "location_source" not in columns
    assert "predicted_class" in columns
    assert "scores" in columns
    assert "confidence" in columns


def test_migration_0013_removes_guide_article_locale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "test_migration_0013.db"
    config = _config(db_path, monkeypatch)
    command.upgrade(config, "head")

    engine = sa.create_engine(f"sqlite:///{db_path}")
    inspector = sa.inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("guide_articles")}
    assert "locale" not in columns
    assert "article_key" in columns
    assert "status" in columns


