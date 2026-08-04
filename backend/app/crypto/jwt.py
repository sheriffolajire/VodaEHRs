"""JWT issue/verify utilities for access and refresh tokens."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings


def create_access_token(subject: str, role: str) -> str:
    """Create a short-lived access token carrying the subject and role claim."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    """Create a long-lived refresh token.

    A random ``jti`` makes each token unique so its stored hash can be rotated
    and revoked independently. Returns the encoded token and its expiry.
    """
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=settings.refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "jti": secrets.token_urlsafe(32),
        "iat": now,
        "exp": expires_at,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt exceptions on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def create_jwt_token(subject: str, role: str, token_type: str = "access") -> str:
    """Create a JWT token with the specified type.

    Args:
        subject: The subject (user_id) of the token.
        role: The user's role.
        token_type: Either "access" or "refresh".

    Returns:
        The encoded JWT token string.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "type": token_type,
    }

    if token_type == "access":
        payload["exp"] = now + timedelta(minutes=settings.access_token_expire_minutes)
    elif token_type == "refresh":
        payload["exp"] = now + timedelta(days=settings.refresh_token_expire_days)
    else:
        raise ValueError(f"Invalid token_type: {token_type}")

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict[str, Any]:
    """Decode and return JWT payload. Raises jwt exceptions on failure.

    Alias for decode_token for consistent naming.
    """
    return decode_token(token)


def verify_jwt_token(token: str) -> bool:
    """Verify a JWT token is valid and not expired.

    Args:
        token: The JWT token string to verify.

    Returns:
        True if the token is valid, False otherwise.
    """
    try:
        decode_token(token)
        return True
    except Exception:
        return False
