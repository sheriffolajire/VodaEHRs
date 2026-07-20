"""Reusable column helpers shared across ORM models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def uuid_pk() -> Mapped[uuid.UUID]:
    """Primary key column using a server-agnostic UUID default."""
    return mapped_column(primary_key=True, default=uuid.uuid4)


def created_at_column() -> Mapped[datetime]:
    """Creation timestamp column defaulting to the current UTC time."""
    return mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
