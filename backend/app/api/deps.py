"""Shared API dependencies (zero-trust enforcement hooks).

The auth guard skeleton
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.crypto.jwt import decode_token

_bearer = HTTPBearer(auto_error=False)


def require_authenticated(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Verify a bearer token is present and valid.

    This is the zero-trust entry point.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    try:
        return decode_token(credentials.credentials)
    except Exception as exc:  
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
