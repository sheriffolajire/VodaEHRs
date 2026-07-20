"""Persistence for refresh tokens (session rotation and revocation)."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


def get_active_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    """Return a refresh token that is neither revoked nor expired."""
    now = datetime.now(UTC)
    return db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )


def add(db: Session, token: RefreshToken) -> RefreshToken:
    db.add(token)
    db.flush()
    return token


def revoke(db: Session, token: RefreshToken) -> None:
    """Mark a refresh token as revoked so it can no longer be used."""
    token.revoked_at = datetime.now(UTC)
    db.flush()
