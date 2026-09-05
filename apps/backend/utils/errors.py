"""Custom exceptions for the application."""

from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API error responses."""

    INVALID_IMAGE = "INVALID_IMAGE"
    MODEL_NOT_READY = "MODEL_NOT_READY"
    INFERENCE_FAILED = "INFERENCE_FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"


class SapiKenalException(Exception):
    """Base exception for SapiKenal application."""


class ModelLoadError(SapiKenalException):
    """Raised when model fails to load."""


class PreprocessingError(SapiKenalException):
    """Raised when image preprocessing fails."""


class InferenceError(SapiKenalException):
    """Raised when model inference fails."""


class InvalidImageError(SapiKenalException):
    """Raised when image is invalid or unsupported."""
