"""Appointment scheduling business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.appointment import Appointment
from app.models.user import User
from app.repositories import appointment_repository
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services import authorization
from app.services.exceptions import ConflictError, NotFoundError


def create_appointment(db: Session, actor: User, payload: AppointmentCreate) -> Appointment:
    """Schedule an appointment, rejecting an exact double-booking."""
    authorization.ensure_patient_access(db, actor, payload.patient_id)

    if appointment_repository.find_conflict(db, payload.clinician_id, payload.scheduled_at):
        raise ConflictError("The clinician already has an appointment at that time.")

    appointment = appointment_repository.add(
        db,
        Appointment(
            patient_id=payload.patient_id,
            clinician_id=payload.clinician_id,
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            reason=payload.reason,
            created_by=actor.id,
        ),
    )
    record_event(
        AuditEvent(
            action="appointment.create",
            user_id=str(actor.id),
            patient_id=str(payload.patient_id),
            status="success",
            reason=str(appointment.id),
        )
    )
    return appointment


def list_appointments(db: Session, actor: User, patient_id: uuid.UUID) -> list[Appointment]:
    """List a patient's appointments after verifying access."""
    authorization.ensure_patient_access(db, actor, patient_id)
    return appointment_repository.list_for_patient(db, patient_id)


def update_appointment(
    db: Session, actor: User, appointment_id: uuid.UUID, payload: AppointmentUpdate
) -> Appointment:
    """Reschedule, cancel, or complete an appointment."""
    appointment = appointment_repository.get_by_id(db, appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    authorization.ensure_patient_access(db, actor, appointment.patient_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.flush()

    record_event(
        AuditEvent(
            action="appointment.update",
            user_id=str(actor.id),
            patient_id=str(appointment.patient_id),
            status="success",
            reason=str(appointment.id),
        )
    )
    return appointment
