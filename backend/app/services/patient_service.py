"""Patient registration, search, and profile business logic."""

import secrets
import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.audit_log import AuditPriority
from app.models.patient import Patient
from app.models.user import User
from app.repositories import patient_repository
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services import authorization
from app.services.audit_service import AuditService
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
    # Log to file (legacy)
    record_event(
        AuditEvent(
            action="patient.register",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    # Persist to database audit log (Phase 5)
    AuditService.persist_audit_entry(
        db=db,
        action="patient.register",
        user_id=actor.id,
        patient_id=patient.id,
        status="success",
        reason=f"Registered patient {patient.first_name} {patient.last_name} ({hospital_number})",
        ip_address=None,
        priority=AuditPriority.NORMAL
    )
    return patient


def search_patients(
    db: Session, actor: User, query: str | None, limit: int, offset: int
) -> list[Patient]:
    """List/search patients scoped to what the actor is allowed to see."""
    allowed_ids = authorization.visible_patient_ids(db, actor)
    patients = patient_repository.search(db, query, limit, offset, only_ids=allowed_ids)
    # Log to file (legacy)
    record_event(AuditEvent(action="patient.search", user_id=str(actor.id), status="success"))
    # Persist to database audit log (Phase 5) - only log if actually searching
    if query:
        AuditService.persist_audit_entry(
            db=db,
            action="patient.search",
            user_id=actor.id,
            patient_id=None,
            status="success",
            reason=f"Searched patients with query: '{query}'",
            ip_address=None,
            priority=AuditPriority.NORMAL
        )
    return patients


def get_patient(db: Session, actor: User, patient_id: uuid.UUID) -> Patient:
    """Return a patient the actor is authorized to view, with an audit entry."""
    patient = authorization.ensure_patient_access(db, actor, patient_id)
    # Log to file (legacy)
    record_event(
        AuditEvent(
            action="patient.view",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    # Persist to database audit log (Phase 5)
    AuditService.persist_audit_entry(
        db=db,
        action="patient.view",
        user_id=actor.id,
        patient_id=patient.id,
        status="success",
        reason=f"Viewed patient {patient.first_name} {patient.last_name} ({patient.hospital_number})",
        ip_address=None,
        priority=AuditPriority.NORMAL
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

    # Log to file (legacy)
    record_event(
        AuditEvent(
            action="patient.update",
            user_id=str(actor.id),
            patient_id=str(patient.id),
            status="success",
        )
    )
    # Persist to database audit log (Phase 5)
    AuditService.persist_audit_entry(
        db=db,
        action="patient.update",
        user_id=actor.id,
        patient_id=patient.id,
        status="success",
        reason=f"Updated patient {patient.first_name} {patient.last_name} ({patient.hospital_number})",
        ip_address=None,
        priority=AuditPriority.NORMAL
    )
    return patient
