"""Resource-level authorization for patient-scoped data.

This is the third link in the zero-trust chain (after identity and role). It
answers a single question: may this user act on this patient? Keeping the rule
in one place stops it drifting as clinical endpoints grow.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository, patient_repository
from app.services.exceptions import NotFoundError, PermissionError_


def ensure_patient_access(db: Session, user: User, patient_id: uuid.UUID) -> Patient:
    """Return the patient if the user may access it, else raise.

    Rules:
      - Admin and Receptionist may access any patient.
      - Doctor and Nurse may access only patients actively assigned to them.
      - Patient may access only their own record (matched by email).
      - Auditor has no patient-data access in this phase.
    """
    patient = patient_repository.get_by_id(db, patient_id)
    if patient is None:
        raise NotFoundError("Patient not found.")

    role = user.role.name

    if role in (RoleName.ADMIN, RoleName.RECEPTIONIST):
        return patient

    if role in (RoleName.DOCTOR, RoleName.NURSE):
        if assignment_repository.get_active(db, patient_id, user.id) is not None:
            return patient
        raise PermissionError_("You are not assigned to this patient.")

    if role == RoleName.PATIENT:
        # A patient is linked to their record by matching email address.
        if patient.email is not None and patient.email == user.email:
            return patient
        raise PermissionError_("You may only access your own record.")

    raise PermissionError_("Your role cannot access patient data.")


def visible_patient_ids(db: Session, user: User) -> list[uuid.UUID] | None:
    """Return the patient-id allowlist for a user, or None for unrestricted.

    Admin and Receptionist see everything (None). Clinicians see their assigned
    patients. Patients and Auditors get an empty list (no list access here).
    """
    role = user.role.name
    if role in (RoleName.ADMIN, RoleName.RECEPTIONIST):
        return None
    if role in (RoleName.DOCTOR, RoleName.NURSE):
        return assignment_repository.list_patient_ids_for_clinician(db, user.id)
    return []
