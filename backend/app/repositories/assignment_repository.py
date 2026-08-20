"""Persistence for patient-clinician assignments."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient_assignment import PatientAssignment


def get_active(
    db: Session, patient_id: uuid.UUID, clinician_id: uuid.UUID
) -> PatientAssignment | None:
    """Return the active assignment for a patient/clinician pair, if any."""
    return db.scalar(
        select(PatientAssignment).where(
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.clinician_id == clinician_id,
            PatientAssignment.revoked_at.is_(None),
        )
    )


def get_by_id(db: Session, assignment_id: uuid.UUID) -> PatientAssignment | None:
    return db.get(PatientAssignment, assignment_id)


def list_patient_ids_for_clinician(db: Session, clinician_id: uuid.UUID) -> list[uuid.UUID]:
    """Return the ids of every patient actively assigned to a clinician."""
    rows = db.scalars(
        select(PatientAssignment.patient_id).where(
            PatientAssignment.clinician_id == clinician_id,
            PatientAssignment.revoked_at.is_(None),
        )
    )
    return list(rows)


def add(db: Session, assignment: PatientAssignment) -> PatientAssignment:
    db.add(assignment)
    db.flush()
    return assignment


def list_for_patient(db: Session, patient_id: uuid.UUID, active_only: bool = True) -> list[PatientAssignment]:
    """Return all assignments for a patient."""
    query = select(PatientAssignment).where(
        PatientAssignment.patient_id == patient_id
    )
    if active_only:
        query = query.where(PatientAssignment.revoked_at.is_(None))
    return list(db.scalars(query).all())


def list_for_clinician(db: Session, clinician_id: uuid.UUID, active_only: bool = True) -> list[PatientAssignment]:
    """Return all assignments for a clinician."""
    query = select(PatientAssignment).where(
        PatientAssignment.clinician_id == clinician_id
    )
    if active_only:
        query = query.where(PatientAssignment.revoked_at.is_(None))
    return list(db.scalars(query).all())


def list_all(db: Session, active_only: bool = True) -> list[PatientAssignment]:
    """Return all assignments."""
    query = select(PatientAssignment)
    if active_only:
        query = query.where(PatientAssignment.revoked_at.is_(None))
    return list(db.scalars(query).all())
