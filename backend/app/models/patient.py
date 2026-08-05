"""Patient demographic and contact model."""

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk

if TYPE_CHECKING:
    from app.models.consent import Consent
    from app.models.emergency_access import EmergencyAccess


class Gender(str, enum.Enum):
    """Patient gender options."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNSPECIFIED = "unspecified"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Human-facing identifier used by hospital staff; unique per patient.
    hospital_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    dob: Mapped[date] = mapped_column(Date)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender, name="gender"))
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # The staff account (Receptionist/Admin) that registered the patient.
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_column()
    
    # Phase 5: Consent relationships
    consents: Mapped[list["Consent"]] = relationship(
        "Consent",
        back_populates="patient",
        lazy="select",
        cascade="all, delete-orphan"
    )
    
    # Phase 5: Emergency access relationships
    emergency_accesses: Mapped[list["EmergencyAccess"]] = relationship(
        "EmergencyAccess",
        back_populates="patient",
        lazy="select",
        cascade="all, delete-orphan"
    )
