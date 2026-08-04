"""Persistence for patients."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.patient import Patient


def get_by_id(db: Session, patient_id: uuid.UUID) -> Patient | None:
    return db.get(Patient, patient_id)


def get_by_hospital_number(db: Session, hospital_number: str) -> Patient | None:
    return db.scalar(select(Patient).where(Patient.hospital_number == hospital_number))


def get_by_email(db: Session, email: str) -> Patient | None:
    return db.scalar(select(Patient).where(Patient.email == email))


def search(
    db: Session,
    query: str | None,
    limit: int,
    offset: int,
    only_ids: list[uuid.UUID] | None = None,
) -> list[Patient]:
    """Search patients by name / hospital number / email.

    When ``only_ids`` is provided the result is restricted to those patients,
    which lets callers apply assigned-patient scoping for clinicians.
    """
    statement = select(Patient)
    if only_ids is not None:
        # An empty allowlist means the caller can see nothing.
        if not only_ids:
            return []
        statement = statement.where(Patient.id.in_(only_ids))
    if query:
        pattern = f"%{query.lower()}%"
        statement = statement.where(
            or_(
                func.lower(Patient.first_name).like(pattern),
                func.lower(Patient.last_name).like(pattern),
                func.lower(Patient.hospital_number).like(pattern),
                func.lower(Patient.email).like(pattern),
            )
        )
    statement = statement.order_by(Patient.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement))


def add(db: Session, patient: Patient) -> Patient:
    db.add(patient)
    db.flush()
    return patient
