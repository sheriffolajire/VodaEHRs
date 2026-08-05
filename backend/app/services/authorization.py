"""Resource-level authorization for patient-scoped data.

This is the third link in the zero-trust chain (after identity and role). It
answers a single question: may this user act on this patient? Keeping the rule
in one place stops it drifting as clinical endpoints grow.

Phase 5 adds the 4th layer: Consent (ensure_consent).
"""

import uuid

from sqlalchemy.orm import Session

from app.models.medical_record import RecordType
from app.models.patient import Patient
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository, consent_repository, emergency_access_repository, patient_repository
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
        # A patient is linked to their record by matching email address
        # or by matching first and last name (for cases where emails differ)
        if patient.email is not None and patient.email == user.email:
            return patient
        # Fallback: match by name
        if (patient.first_name.lower() == user.first_name.lower() and 
            patient.last_name.lower() == user.last_name.lower()):
            return patient
        raise PermissionError_("You may only access your own record.")

    raise PermissionError_("Your role cannot access patient data.")


def ensure_consent(
    db: Session,
    clinician: User,
    patient_id: uuid.UUID,
    record_type: RecordType,
    is_admin_override: bool = False
) -> bool:
    """Check if clinician has consent OR active break-glass for this record type.
    
    This is Layer 4 of the Zero-Trust chain:
    1. Identity (JWT token)
    2. Role (require_role)
    3. Resource Access (ensure_patient_access) ← Previous layer
    4. Consent (ensure_consent) ← THIS FUNCTION
    5. Integrity (decrypt + verify)
    
    Break-glass explicitly bypasses this layer only, with:
    - Mandatory reason
    - 30-minute expiry
    - High-priority audit
    
    Args:
        db: Database session
        clinician: The clinician requesting access
        patient_id: The patient whose records are being accessed
        record_type: Type of record being accessed
        is_admin_override: If True, admin is bypassing consent (still audited)
    
    Returns:
        True if access is granted (consent or break-glass or admin override)
    
    Raises:
        PermissionError_: If no consent, no break-glass, and no admin override
    """
    # Patients always have access to their own records
    if clinician.role.name == RoleName.PATIENT:
        # Check if accessing own record
        patient = patient_repository.get_by_id(db, patient_id)
        if patient and patient.email == clinician.email:
            return True
        raise PermissionError_("You may only access your own record.")
    
    # Admins can override but must be explicitly audited
    if is_admin_override and clinician.role.name == RoleName.ADMIN:
        return True  # Caller must audit this as "admin_override"
    
    # Check active consent
    has_consent = consent_repository.has_active_consent(
        db, patient_id, clinician.id, record_type
    )
    
    if has_consent:
        return True
    
    # Check active break-glass (emergency access)
    has_emergency = emergency_access_repository.has_active_emergency_access(
        db, clinician.id, patient_id
    )
    
    if has_emergency:
        return True
    
    # No consent, no break-glass
    raise PermissionError_(
        f"No consent granted for {record_type.value} records. "
        "Request patient consent or use break-glass in emergency."
    )


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
