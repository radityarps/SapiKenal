"""SQLAlchemy engine and request-scoped session helpers."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from config import settings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _prepare_sqlite_path(database_url: str) -> None:
    """Create the parent directory for a relative/file SQLite URL."""
    if not database_url.startswith("sqlite") or ":memory:" in database_url:
        return
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        raw_path = database_url[len(prefix) :]
        if raw_path.startswith("/"):
            path = Path(raw_path)
        else:
            path = Path.cwd() / raw_path
        path.parent.mkdir(parents=True, exist_ok=True)


def build_engine(database_url: str | None = None) -> Engine:
    """Build an engine for SQLite development or PostgreSQL deployment."""
    url = database_url or settings.database_url
    _prepare_sqlite_path(url)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = build_engine()
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def get_db() -> Generator[Session, None, None]:
    """Yield one SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
