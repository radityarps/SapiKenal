"""Schemas for the protected admin API."""

from datetime import datetime
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class PageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[Any]


class UserCreateRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    role: Literal["user", "admin"] = "user"
    password: str | None = Field(default=None, min_length=1, max_length=256)


class UserPatchRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Literal["user", "admin"] | None = None
    status: Literal["active", "inactive", "locked"] | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str
    role: str
    status: str
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserMutationResponse(BaseModel):
    status: str = "success"
    user: UserResponse
    temporary_password: str | None = None


class PredictionResponse(BaseModel):
    id: int | str
    device_ref: str
    user_id: str | None
    timestamp: int
    predicted_class: str | None
    display_label: str
    confidence: float
    scores: dict[str, float] = Field(default_factory=dict)
    inference_mode: str
    processing_ms: int | None
    app_version: str | None
    model_version: str | None
    status: Literal["success", "failed"]
    error_code: str | None = None


class DashboardPeriod(BaseModel):
    key: Literal["24h", "7d", "30d"]
    start_timestamp: int
    end_timestamp: int


def _article_sources(value: list[str]) -> list[str]:
    sources = [source.strip() for source in value]
    if any(
        not source
        or any(character.isspace() for character in source)
        or (parsed := urlsplit(source)).scheme not in {"http", "https"}
        or not parsed.hostname
        for source in sources
    ):
        raise ValueError("Sources must be valid HTTP(S) URLs")
    return sources


class GuideArticleRequest(BaseModel):
    article_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$",
    )
    locale: Literal["id-ID", "en-US"] = "id-ID"
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
    sort_order: int = Field(default=0, ge=0, le=100_000)
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=50_000)
    sources: list[str] = Field(min_length=1, max_length=20)
    content_reviewed: Literal[False] = False

    @field_validator("article_key", "icon", "title", "summary", "body")
    @classmethod
    def non_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Article text must not be blank")
        return value

    @field_validator("sources")
    @classmethod
    def valid_sources(cls, value: list[str]) -> list[str]:
        return _article_sources(value)


class GuideArticlePatchRequest(BaseModel):
    article_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$",
    )
    locale: Literal["id-ID", "en-US"] | None = None
    category: (
        Literal[
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
        | None
    ) = None
    icon: str | None = Field(default=None, min_length=1, max_length=16)
    sort_order: int | None = Field(default=None, ge=0, le=100_000)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, min_length=1, max_length=50_000)
    sources: list[str] | None = Field(default=None, min_length=1, max_length=20)
    content_reviewed: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_fields(cls, value: Any) -> Any:
        if isinstance(value, dict) and any(item is None for item in value.values()):
            raise ValueError("Article patch fields must not be null")
        return value

    @field_validator("article_key", "icon", "title", "summary", "body")
    @classmethod
    def non_blank_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Article text must not be blank")
        return value

    @field_validator("sources")
    @classmethod
    def valid_sources(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else _article_sources(value)


class GuideArticleRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    revision: int
    category: str
    icon: str
    sort_order: int
    title: str
    summary: str
    body: str
    sources: list[str]
    content_reviewed: bool
    status: str
    created_at: datetime
    updated_at: datetime


class GuideArticleLocalePairResponse(BaseModel):
    locale: Literal["id-ID", "en-US"]
    status: Literal["missing", "inactive", "active"]


class GuideArticleResponse(BaseModel):
    id: str
    article_key: str
    locale: str
    publication_status: Literal["draft", "active", "inactive"]
    revision: GuideArticleRevisionResponse
    active_revision: GuideArticleRevisionResponse | None
    locale_pair: GuideArticleLocalePairResponse | None = None
    created_at: datetime
    updated_at: datetime


class ModelRegisterRequest(BaseModel):
    version: str = Field(min_length=1, max_length=128)
    artifact_name: str = Field(min_length=1, max_length=255, pattern=r"^[^/\\\\]+$")
    checksum: str = Field(min_length=64, max_length=128, pattern=r"^[0-9a-fA-F]+$")
    input_size: int = Field(default=224, ge=1, le=4096)
    classes: list[str] = Field(min_length=1, max_length=32)
    metrics: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=10_000)


class ModelActivationRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1_000)

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError(
                "Reason must contain at least three non-whitespace characters"
            )
        return value


class ModelVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    artifact_name: str
    checksum: str
    status: str
    input_size: int
    classes: list[str]
    metrics: dict[str, Any] | None
    notes: str | None
    registered_at: datetime
    activated_at: datetime | None
    deactivated_at: datetime | None
    rolled_back_at: datetime | None
    activated_by: str | None
    compatible: bool = True


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str | None
    actor_display_name: str | None = None
    action: str
    resource_type: str | None
    resource_id: str | None
    request_id: str | None
    status: str
    changed_fields: dict[str, Any] | None
    reason: str | None
    created_at: datetime
