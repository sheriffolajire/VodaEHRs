"""Patient-clinician assignment business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.patient_assignment import PatientAssignment
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository, patient_repository, user_repository
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


def assign(
    db: Session, patient_id: uuid.UUID, clinician_id: uuid.UUID, actor: User
) -> PatientAssignment:
    """Assign a clinician (Doctor/Nurse) to a patient."""
    if patient_repository.get_by_id(db, patient_id) is None:
        raise NotFoundError("Patient not found.")

    clinician = user_repository.get_by_id(db, clinician_id)
    if clinician is None:
        raise NotFoundError("Clinician not found.")
    if clinician.role.name not in (RoleName.DOCTOR, RoleName.NURSE):
        raise ValidationError("Only doctors and nurses can be assigned to patients.")

    if assignment_repository.get_active(db, patient_id, clinician_id) is not None:
        raise ConflictError("This clinician is already assigned to the patient.")

    assignment = assignment_repository.add(
        db,
        PatientAssignment(
            patient_id=patient_id,
            clinician_id=clinician_id,
            assigned_by=actor.id,
        ),
    )
    record_event(
        AuditEvent(
            action="patient.assign",
            user_id=str(actor.id),
            patient_id=str(patient_id),
            status="success",
            reason=str(clinician_id),
        )
    )
    return assignment


def revoke(db: Session, assignment_id: uuid.UUID, actor: User) -> None:
    """Revoke an active assignment."""
    from datetime import UTC, datetime

    assignment = assignment_repository.get_by_id(db, assignment_id)
    if assignment is None or assignment.revoked_at is not None:
        raise NotFoundError("Assignment not found.")

    assignment.revoked_at = datetime.now(UTC)
    db.flush()
    record_event(
        AuditEvent(
            action="patient.unassign",
            user_id=str(actor.id),
            patient_id=str(assignment.patient_id),
            status="success",
        )
    )
