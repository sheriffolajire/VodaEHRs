"""Role model and the canonical set of Voda roles."""

import enum
import uuid

from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import uuid_pk


class RoleName(str, enum.Enum):
    """The fixed set of roles defined by the RBAC engine."""

    ADMIN = "Admin"
    DOCTOR = "Doctor"
    NURSE = "Nurse"
    PATIENT = "Patient"
    RECEPTIONIST = "Receptionist"
    AUDITOR = "Auditor"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = uuid_pk()
    # The role name is the stable identifier used in JWT claims and RBAC checks.
    name: Mapped[RoleName] = mapped_column(SQLEnum(RoleName, name="role_name"), unique=True)
