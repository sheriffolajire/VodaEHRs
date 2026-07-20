"""Authentication and session business logic.

Coordinates password verification, token issuance/rotation, password reset, and
audit logging. Persistence lives in repositories; transport concerns live in the
router.
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.core.config import settings
from app.crypto.hashing import hash_password, verify_password
from app.crypto.jwt import create_access_token, create_refresh_token, decode_token
from app.crypto.password_policy import PasswordPolicyError, validate_password
from app.crypto.tokens import hash_token
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserStatus
from app.repositories import (
    password_reset_repository,
    refresh_token_repository,
    user_repository,
)
from app.services.exceptions import AuthError, ValidationError


def _issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    """Create an access/refresh token pair and persist the refresh token hash."""
    access_token = create_access_token(subject=str(user.id), role=user.role.name.value)
    refresh_token, expires_at = create_refresh_token(subject=str(user.id))
    refresh_token_repository.add(
        db,
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        ),
    )
    return access_token, refresh_token


def login(db: Session, email: str, password: str, ip_address: str | None) -> tuple[str, str, User]:
    """Authenticate a user and return an access/refresh token pair.

    A single generic error is used for every failure mode so the endpoint does
    not reveal whether an email exists or an account is disabled.
    """
    user = user_repository.get_by_email(db, email)
    invalid = user is None or user.status != UserStatus.ACTIVE
    # Always run verification against a real or dummy hash to keep timing uniform.
    password_ok = verify_password(password, user.password_hash) if user else False

    if invalid or not password_ok:
        record_event(
            AuditEvent(
                action="auth.login",
                user_id=str(user.id) if user else None,
                status="failure",
                reason="invalid_credentials",
                ip_address=ip_address,
            )
        )
        raise AuthError("Invalid email or password.")

    access_token, refresh_token = _issue_token_pair(db, user)
    record_event(
        AuditEvent(
            action="auth.login", user_id=str(user.id), status="success", ip_address=ip_address
        )
    )
    return access_token, refresh_token, user


def refresh(db: Session, refresh_token: str, ip_address: str | None) -> tuple[str, str, User]:
    """Rotate a refresh token: validate, revoke the old, issue a new pair."""
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001 - normalized to an auth error
        raise AuthError("Invalid refresh token.") from exc

    if payload.get("type") != "refresh":
        raise AuthError("Invalid refresh token.")

    stored = refresh_token_repository.get_active_by_hash(db, hash_token(refresh_token))
    if stored is None:
        raise AuthError("Refresh token is no longer valid.")

    user = user_repository.get_by_id(db, uuid.UUID(payload["sub"]))
    if user is None or user.status != UserStatus.ACTIVE:
        raise AuthError("Account is not active.")

    # One-time use: revoke the presented token before issuing its replacement.
    refresh_token_repository.revoke(db, stored)
    access_token, new_refresh = _issue_token_pair(db, user)
    record_event(
        AuditEvent(
            action="auth.refresh", user_id=str(user.id), status="success", ip_address=ip_address
        )
    )
    return access_token, new_refresh, user


def logout(db: Session, refresh_token: str, ip_address: str | None) -> None:
    """Revoke the presented refresh token if it is still active."""
    stored = refresh_token_repository.get_active_by_hash(db, hash_token(refresh_token))
    if stored is not None:
        refresh_token_repository.revoke(db, stored)
        record_event(
            AuditEvent(
                action="auth.logout",
                user_id=str(stored.user_id),
                status="success",
                ip_address=ip_address,
            )
        )


def request_password_reset(db: Session, email: str, ip_address: str | None) -> str | None:
    """Create a reset token for an existing active user.

    Returns the raw token for out-of-band delivery, or None if no eligible user
    exists. The caller always responds identically to avoid account enumeration.
    """
    user = user_repository.get_by_email(db, email)
    if user is None or user.status != UserStatus.ACTIVE:
        return None

    raw_token = secrets.token_urlsafe(32)
    password_reset_repository.add(
        db,
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_expire_minutes),
        ),
    )
    record_event(
        AuditEvent(
            action="auth.password_reset_request",
            user_id=str(user.id),
            status="success",
            ip_address=ip_address,
        )
    )
    return raw_token


def confirm_password_reset(
    db: Session, token: str, new_password: str, ip_address: str | None
) -> None:
    """Validate a reset token, apply the new password, and consume the token."""
    stored = password_reset_repository.get_valid_by_hash(db, hash_token(token))
    if stored is None:
        raise AuthError("Reset token is invalid or has expired.")

    try:
        validate_password(new_password)
    except PasswordPolicyError as exc:
        raise ValidationError(str(exc)) from exc

    user = user_repository.get_by_id(db, stored.user_id)
    if user is None:
        raise AuthError("Reset token is invalid or has expired.")

    user.password_hash = hash_password(new_password)
    password_reset_repository.mark_used(db, stored)
    record_event(
        AuditEvent(
            action="auth.password_reset_confirm",
            user_id=str(user.id),
            status="success",
            ip_address=ip_address,
        )
    )
