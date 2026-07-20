"""Persistence for single-use password reset tokens."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken


def get_valid_by_hash(db: Session, token_hash: str) -> PasswordResetToken | None:
    """Return a reset token that has not been used and has not expired."""
    now = datetime.now(UTC)
    return db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )


def add(db: Session, token: PasswordResetToken) -> PasswordResetToken:
    db.add(token)
    db.flush()
    return token


def mark_used(db: Session, token: PasswordResetToken) -> None:
    token.used_at = datetime.now(UTC)
    db.flush()
