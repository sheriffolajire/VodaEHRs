"""User account model."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk
from app.models.role import Role


class UserStatus(str, enum.Enum):
    """Account status. Disabled accounts cannot authenticate."""

    ACTIVE = "active"
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Argon2id hash only; the plaintext password is never stored.
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status"), default=UserStatus.ACTIVE
    )
    created_at: Mapped[datetime] = created_at_column()

    role: Mapped[Role] = relationship(lazy="joined")
    key_pair: Mapped["UserKey"] = relationship(
        "UserKey", back_populates="user", uselist=False
    )
