"""Standard API response envelope and shared schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success envelope: {success, message, data}."""

    success: bool = True
    message: str = ""
    data: T | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard failure envelope: {success, message, errors}."""

    success: bool = False
    message: str = ""
    errors: list[ErrorDetail] = []


def success(data: Any = None, message: str = "") -> dict[str, Any]:
    """Build a standard success payload."""
    return {"success": True, "message": message, "data": data}


def failure(message: str, errors: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build a standard failure payload."""
    return {"success": False, "message": message, "errors": errors or []}
