"""Schemas for the protected admin MVP API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
    predicted_class: str
    display_label: str
    confidence: float
    scores: dict[str, float] = Field(default_factory=dict)
    outcome: Literal["accepted", "rejected", "failed"] = "accepted"
    rejection_reason: str | None = None
    is_reliable: bool
    inference_mode: str
    processing_ms: int | None
    app_version: str | None
    model_version: str | None
    status: str = "success"
    error_code: str | None = None


class DashboardPeriod(BaseModel):
    key: Literal["24h", "7d", "30d"]
    start_timestamp: int
    end_timestamp: int


class DiseaseContentRequest(BaseModel):
    slug: str = Field(
        min_length=1, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    model_class: str | None = Field(default=None, max_length=32)
    display_name: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=10_000)
    handling_advice: str = Field(min_length=1, max_length=10_000)
    disclaimer: str = Field(min_length=1, max_length=1_000)
    locale: str = Field(default="id-ID", min_length=2, max_length=16)


class DiseaseContentPatchRequest(BaseModel):
    model_class: str | None = Field(default=None, max_length=32)
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    handling_advice: str | None = Field(default=None, min_length=1, max_length=10_000)
    disclaimer: str | None = Field(default=None, min_length=1, max_length=1_000)


class DiseaseRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    revision: int
    model_class: str | None
    display_name: str
    summary: str
    description: str
    handling_advice: str
    disclaimer: str
    status: str
    created_at: datetime
    updated_at: datetime


class DiseaseContentResponse(BaseModel):
    id: str
    slug: str
    locale: str
    status: str
    revision: DiseaseRevisionResponse
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
