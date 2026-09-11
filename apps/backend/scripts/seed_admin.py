"""Create or explicitly rotate the first admin account.

Usage is documented in the repository PRD. Credentials default to
ADMIN_EMAIL (admin@example.com), ADMIN_PASSWORD (password), and ADMIN_NAME (Administrator).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import (  # pyright: ignore[reportMissingImports]
    BaseModel,
    EmailStr,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)
from sqlalchemy import inspect, select  # pyright: ignore[reportMissingImports]
from sqlalchemy.exc import SQLAlchemyError  # pyright: ignore[reportMissingImports]

from api.auth_security import hash_password, revoke_all_sessions, validate_password
from config import settings
from db.core import SessionLocal, engine
from db.models import GuideArticle, GuideArticleRevision, User
from services.audit import record_audit

GUIDE_ARTICLE_SEED_PATH = (
    Path(__file__).parents[1] / "data" / "guide_articles_seed.json"
)


def _admin_credentials(
    *, allow_weak_password: bool = False
) -> tuple[EmailStr, str, str]:
    raw_email = (
        os.getenv("ADMIN_EMAIL", "admin@example.com").strip() or "admin@example.com"
    )
    try:
        email = TypeAdapter(EmailStr).validate_python(raw_email)
    except ValidationError as exc:
        raise ValueError("ADMIN_EMAIL must be a valid email address") from exc
    password = os.getenv("ADMIN_PASSWORD", "password").strip() or "password"
    display_name = os.getenv("ADMIN_NAME", "Administrator").strip() or "Administrator"
    if allow_weak_password:
        if settings.fastapi_env != "development" or not settings.debug:
            raise ValueError(
                "--allow-weak-password is only available in development with DEBUG=true"
            )
    else:
        validate_password(password)
    return email, password, display_name


class GuideArticleSeed(BaseModel):
    article_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$",
    )
    locale: Literal["id-ID", "en-US"]
    category: Literal[
        "app_usage",
        "aceh",
        "bali",
        "brahman",
        "brangus",
        "limusin",
        "madura",
        "pasundan",
        "po",
    ]
    icon: str = Field(min_length=1, max_length=16)
    sort_order: int = Field(ge=0, le=100_000)
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=50_000)
    sources: list[str] = Field(max_length=20)

    @field_validator("article_key", "icon", "title", "summary", "body")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("article text must not be blank")
        return value

    @field_validator("sources")
    @classmethod
    def valid_sources(cls, sources: list[str]) -> list[str]:
        for source in sources:
            parsed = urlsplit(source)
            if (
                not source
                or len(source) > 2_048
                or any(character.isspace() for character in source)
                or parsed.scheme not in {"http", "https"}
                or not parsed.hostname
            ):
                raise ValueError("sources must contain only HTTP(S) URLs")
        return sources


def _guide_article_seeds(path: Path) -> list[GuideArticleSeed]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Guide article seed is unreadable: {path}") from exc
    if not isinstance(raw, list):
        raise RuntimeError(f"Guide article seed root must be a list: {path}")
    if len(raw) > 200:
        raise RuntimeError(f"Guide article seed exceeds 200 items: {path}")

    seeds: list[GuideArticleSeed] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(raw):
        try:
            seed = GuideArticleSeed.model_validate(item)
        except ValidationError as exc:
            raise RuntimeError(
                f"Guide article seed item {index} is invalid in {path}: {exc}"
            ) from exc
        identity = (seed.article_key, seed.locale)
        if identity in seen:
            raise RuntimeError(
                f"Guide article seed item {index} duplicates "
                f"({seed.article_key}, {seed.locale}) in {path}"
            )
        seen.add(identity)
        seeds.append(seed)
    return seeds


def seed_guide_articles() -> int:
    """Insert bundled articles as unreviewed drafts without changing existing CMS data."""
    path = GUIDE_ARTICLE_SEED_PATH
    seeds = _guide_article_seeds(path)
    created = 0
    try:
        with SessionLocal() as db:
            for seed in seeds:
                existing = db.scalar(
                    select(GuideArticle).where(
                        GuideArticle.article_key == seed.article_key,
                        GuideArticle.locale == seed.locale,
                    )
                )
                if existing is not None:
                    continue
                article = GuideArticle(
                    article_key=seed.article_key,
                    locale=seed.locale,
                    status="draft",
                )
                db.add(article)
                db.flush()
                db.add(
                    GuideArticleRevision(
                        article_id=article.id,
                        revision=1,
                        category=seed.category,
                        icon=seed.icon,
                        sort_order=seed.sort_order,
                        title=seed.title,
                        summary=seed.summary,
                        body=seed.body,
                        sources=seed.sources,
                        content_reviewed=False,
                        status="draft",
                    )
                )
                created += 1
            db.commit()
    except SQLAlchemyError as exc:
        raise RuntimeError(f"Guide article seed could not be stored: {path}") from exc
    return created


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
        print(f"guide article drafts created: {seed_guide_articles()}")
    except (RuntimeError, ValueError) as exc:
        print(f"seed-admin failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
