"""Pydantic schemas for mobile backend contract."""

from enum import Enum
from math import isclose, isfinite
from typing import Any, Literal

from config import canonicalize_label
from pydantic import BaseModel, Field, model_validator

_CANONICAL_SCORE_KEYS = ("FMD", "healthy", "LSD", "non_cattle")


class DiseaseClass(str, Enum):
    FMD = "FMD"
    LSD = "LSD"
    HEALTHY = "healthy"
    NON_CATTLE = "non_cattle"


class PredictionResult(BaseModel):
    outcome: Literal["accepted", "rejected"] = "accepted"
    disease_class: DiseaseClass
    display_label_key: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_reliable: bool
    scores: dict[str, float]


class ModelInfo(BaseModel):
    version: str


class PredictResponse(BaseModel):
    status: str = "success"
    prediction: PredictionResult
    model_info: ModelInfo
    processing_time_ms: int = Field(ge=0)
    preprocessing_time_ms: int = Field(ge=0)
    inference_time_ms: int = Field(ge=0)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str = Field(max_length=256)
    rejection: dict[str, Any] | None = None
    model_info: ModelInfo | None = None
    processing_time_ms: int | None = Field(default=None, ge=0)
    preprocessing_time_ms: int | None = Field(default=None, ge=0)
    inference_time_ms: int | None = Field(default=None, ge=0)


class HistoryCreate(BaseModel):
    device_id: str = Field(min_length=8, max_length=128)
    local_id: int | None = None
    timestamp: int
    predicted_class: DiseaseClass
    display_label: str = Field(min_length=1, max_length=128)
    confidence: float = Field(ge=0.0, le=1.0)
    scores: dict[str, float] = Field(default_factory=dict)
    outcome: Literal["accepted", "rejected"] = "accepted"
    rejection_reason: Literal["non_cattle"] | None = None
    inference_mode: str = Field(min_length=1, max_length=32)
    is_reliable: bool
    processing_ms: int | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    consent_status: str | None = Field(default=None, max_length=32)
    app_version: str | None = Field(default=None, max_length=64)
    model_version: str | None = Field(default=None, max_length=128)
    image_source: str | None = Field(default=None, max_length=32)
    preprocessing_summary: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_source: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def validate_outcome_contract(self) -> "HistoryCreate":
        normalized_scores: dict[str, float] = {}
        for raw_label, raw_score in self.scores.items():
            label = canonicalize_label(raw_label)
            if label not in _CANONICAL_SCORE_KEYS:
                raise ValueError(f"Unknown model score label: {raw_label}")
            try:
                score = float(raw_score)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid model score for label: {raw_label}") from exc
            if not isfinite(score) or not 0 <= score <= 1:
                raise ValueError(
                    f"Model score must be finite and between 0 and 1: {raw_label}"
                )
            normalized_scores[label] = score

        missing = [key for key in _CANONICAL_SCORE_KEYS if key not in normalized_scores]
        if missing == ["non_cattle"] and self.outcome == "accepted":
            # Accept three-score payloads from older mobile clients during migration.
            normalized_scores["non_cattle"] = 0.0
        elif missing:
            raise ValueError("Scores must contain all four canonical model classes")

        predicted_class = self.predicted_class.value
        if self.outcome == "rejected":
            if predicted_class != "non_cattle":
                raise ValueError("Rejected history must use predicted_class=non_cattle")
            if self.rejection_reason != "non_cattle":
                raise ValueError(
                    "Rejected history must use rejection_reason=non_cattle"
                )
            if self.is_reliable:
                raise ValueError("Rejected non-cattle history cannot be reliable")
        elif predicted_class == "non_cattle":
            raise ValueError("Accepted history cannot use predicted_class=non_cattle")
        elif self.rejection_reason is not None:
            raise ValueError("Accepted history cannot have a rejection reason")

        if normalized_scores and not isclose(
            sum(normalized_scores.values()),
            1.0,
            abs_tol=0.01,
        ):
            raise ValueError("Model scores must sum to one")
        if normalized_scores and not isclose(
            self.confidence,
            max(normalized_scores.values()),
            abs_tol=0.01,
        ):
            raise ValueError("Confidence must match the highest model score")
        self.scores = normalized_scores
        return self


class HistoryRecord(HistoryCreate):
    id: int
    created_at: int
    updated_at: int

    @classmethod
    def from_row(cls, row: dict) -> "HistoryRecord":
        row_data = dict(row)
        outcome = row_data.pop("outcome", "accepted")
        rejection_reason = row_data.pop("rejection_reason", None)
        return cls(
            **row_data,
            scores={
                "healthy": row.get("score_healthy", 0),
                "FMD": row.get("score_fmd", 0),
                "LSD": row.get("score_lsd", 0),
                "non_cattle": row.get("score_non_cattle", 0),
            },
            outcome=outcome,
            rejection_reason=rejection_reason,
        )


class HistoryListResponse(BaseModel):
    status: str = "success"
    items: list[HistoryRecord]


class HistoryUpsertResponse(BaseModel):
    status: str = "success"
    item: HistoryRecord
