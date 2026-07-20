"""Shared API dependencies (zero-trust enforcement hooks).

Phase 2 activates the first two layers of the zero-trust chain: identity
(valid access token) and authorization (role check). Consent and record
decryption are layered in later phases.
"""

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.crypto.jwt import decode_token
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User, UserStatus
from app.repositories import user_repository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated, active user from a valid access token.

    This is the zero-trust entry point. It rejects missing, malformed, expired,
    or non-access tokens, and accounts that no longer exist or are disabled.
    """
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.")

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001 - normalized to 401 at the boundary
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.") from exc

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type.")

    user = user_repository.get_by_id(db, uuid.UUID(payload["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account is not active.")
    return user


def require_role(*allowed_roles: RoleName) -> Callable[[User], User]:
    """Build a dependency that allows only the given roles.

    Authorization is always enforced server-side; the frontend role checks are
    for user experience only.
    """

    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions.")
        return current_user

    return _guard
