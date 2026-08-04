"""Patient registration, search, and profile business logic."""

import secrets
import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.patient import Patient
from app.models.user import User
from app.repositories import patient_repository
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services import authorization
from app.services.exceptions import ConflictError, NotFoundError


def _generate_hospital_number() -> str:
    """Generate a unique, human-readable hospital number."""
    return f"VOD-{secrets.randbelow(1_000_000):06d}"


def register_patient(db: Session, payload: PatientCreate, actor: User) -> Patient:
    """Register a new patient, generating a hospital number when not supplied."""
    hospital_number = payload.hospital_number or _generate_hospital_number()
    if patient_repository.get_by_hospital_number(db, hospital_number) is not None:
        raise ConflictError("A patient with this hospital number already exists.")

    patient = patient_repository.add(
        db,
        Patient(
            hospital_number=hospital_number,
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            gender=payload.gender,
            email=payload.email,
            phone=payload.phone,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            created_by=actor.id,
        ),
    )
    record_event(
        AuditEvent(
            action="patient.register",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    return patient


def search_patients(
    db: Session, actor: User, query: str | None, limit: int, offset: int
) -> list[Patient]:
    """List/search patients scoped to what the actor is allowed to see."""
    allowed_ids = authorization.visible_patient_ids(db, actor)
    patients = patient_repository.search(db, query, limit, offset, only_ids=allowed_ids)
    record_event(AuditEvent(action="patient.search", user_id=str(actor.id), status="success"))
    return patients


def get_patient(db: Session, actor: User, patient_id: uuid.UUID) -> Patient:
    """Return a patient the actor is authorized to view, with an audit entry."""
    patient = authorization.ensure_patient_access(db, actor, patient_id)
    record_event(
        AuditEvent(
            action="patient.view",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    return patient


def update_patient(
    db: Session, actor: User, patient_id: uuid.UUID, payload: PatientUpdate
) -> Patient:
    """Update mutable patient profile fields."""
    patient = patient_repository.get_by_id(db, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.flush()

    record_event(
        AuditEvent(
            action="patient.update",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    return patient
