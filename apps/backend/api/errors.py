"""Errors for standardized admin/auth API responses."""

from typing import Any

from fastapi import HTTPException


class AdminAPIError(HTTPException):
    """An error rendered using the admin API error contract."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field_errors: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "field_errors": field_errors or {},
            },
        )
