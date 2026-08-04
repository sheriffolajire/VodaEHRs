"""Persistence for appointments."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus


def get_by_id(db: Session, appointment_id: uuid.UUID) -> Appointment | None:
    return db.get(Appointment, appointment_id)


def list_for_patient(db: Session, patient_id: uuid.UUID) -> list[Appointment]:
    return list(
        db.scalars(
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.scheduled_at)
        )
    )


def list_for_clinician(db: Session, clinician_id: uuid.UUID) -> list[Appointment]:
    return list(
        db.scalars(
            select(Appointment)
            .where(Appointment.clinician_id == clinician_id)
            .order_by(Appointment.scheduled_at)
        )
    )


def find_conflict(
    db: Session, clinician_id: uuid.UUID, scheduled_at: datetime
) -> Appointment | None:
    """Return a scheduled appointment for the clinician at the same start time."""
    return db.scalar(
        select(Appointment).where(
            Appointment.clinician_id == clinician_id,
            Appointment.scheduled_at == scheduled_at,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
    )


def add(db: Session, appointment: Appointment) -> Appointment:
    db.add(appointment)
    db.flush()
    return appointment
