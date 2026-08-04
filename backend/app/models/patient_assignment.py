"""Join model linking clinicians to the patients they may access."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import uuid_pk


class PatientAssignment(Base):
    __tablename__ = "patient_assignments"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    clinician_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    # The staff account (Admin/Receptionist) that created the assignment.
    assigned_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # A non-null revoked_at ends the assignment without deleting its history.
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Speeds up the common "is this clinician assigned to this patient?" lookup.
    __table_args__ = (Index("ix_assignment_patient_clinician", "patient_id", "clinician_id"),)
