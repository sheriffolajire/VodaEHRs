"""Maps service-layer exceptions to HTTP errors.

Keeping this in one place lets every router translate domain failures into the
standard envelope consistently (the global handler formats the body).
"""

from fastapi import HTTPException, status

from app.services.exceptions import (
    ConflictError,
    CryptoError,
    NotFoundError,
    PermissionError_,
    ValidationError,
)


def to_http_error(exc: Exception) -> HTTPException:
    """Return the HTTPException that matches a domain exception."""
    if isinstance(exc, NotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    if isinstance(exc, PermissionError_):
        return HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    if isinstance(exc, ConflictError):
        return HTTPException(status.HTTP_409_CONFLICT, str(exc))
    if isinstance(exc, ValidationError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    if isinstance(exc, CryptoError):
        return HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Cryptographic operation failed: {str(exc)}")
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
