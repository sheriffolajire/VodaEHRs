"""Resource-level authorization for patient-scoped data.

This is the third link in the zero-trust chain (after identity and role). It
answers a single question: may this user act on this patient? Keeping the rule
in one place stops it drifting as clinical endpoints grow.

Phase 5 adds the 4th layer: Consent (ensure_consent).
"""

import enum
import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.medical_record import RecordType
from app.models.patient import Patient
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository, consent_repository, emergency_access_repository, patient_repository
from app.services.exceptions import NotFoundError, PermissionError_

logger = get_logger("authorization")


class ResourceType(str, enum.Enum):
    """Resource types for consent and authorization checks.
    
    Extends RecordType to include documents and appointments.
    """
    # Record types
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    NURSING_NOTE = "nursing_note"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    OTHER = "other"
    
    # Document types
    DOCUMENT = "document"
    
    # Appointment type
    APPOINTMENT = "appointment"


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
    record_type: RecordType | ResourceType,
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
        record_type: Type of record being accessed (RecordType or ResourceType)
        is_admin_override: If True, admin is bypassing consent (still audited)
    
    Returns:
        True if access is granted (consent or break-glass or admin override)
    
    Raises:
        PermissionError_: If no consent, no break-glass, and no admin override
    """
    # Convert RecordType to string value for comparison
    record_type_str = record_type.value if hasattr(record_type, 'value') else str(record_type)
    
    # Patients always have access to their own records
    if clinician.role.name == RoleName.PATIENT:
        # Check if accessing own record by email or name match
        patient = patient_repository.get_by_id(db, patient_id)
        if patient:
            # Match by email (exact or if patient record email matches user email)
            if patient.email == clinician.email:
                return True
            # Match by name (for cases where emails differ)
            if (patient.first_name and patient.last_name and 
                clinician.first_name and clinician.last_name and
                patient.first_name.lower() == clinician.first_name.lower() and
                patient.last_name.lower() == clinician.last_name.lower()):
                return True
        raise PermissionError_("You may only access your own record.")
    
    # Admins can override but must be explicitly audited
    if is_admin_override and clinician.role.name == RoleName.ADMIN:
        return True  # Caller must audit this as "admin_override"
    
    # Check active consent using the string value
    from app.models.consent import Consent
    from datetime import datetime
    from sqlalchemy import or_
    
    now = datetime.utcnow()
    
    logger.info(f"Checking consent for clinician={clinician.id}, patient={patient_id}, record_type={record_type_str}")
    
    # First, check if ANY consent exists for this patient/clinician
    any_consent = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.clinician_id == clinician.id
    ).first()
    
    if any_consent:
        logger.info(f"Found consent record: id={any_consent.id}, record_type={any_consent.record_type}, granted={any_consent.granted}, revoked_at={any_consent.revoked_at}, expires_at={any_consent.expires_at}")
    else:
        logger.info(f"No consent record found for clinician={clinician.id}, patient={patient_id}")
    
    active_consent = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.clinician_id == clinician.id,
        Consent.record_type == record_type_str,
        Consent.granted == True,
        Consent.revoked_at.is_(None),
        or_(
            Consent.expires_at.is_(None),
            Consent.expires_at > now
        )
    ).first()
    
    if active_consent:
        logger.info(f"Active consent found: {active_consent.id}")
        return True
    else:
        logger.info(f"No active consent found for record_type={record_type_str}")
    
    # Check active break-glass (emergency access)
    has_emergency = emergency_access_repository.has_active_emergency_access(
        db, clinician.id, patient_id
    )
    
    if has_emergency:
        return True
    
    # No consent, no break-glass
    raise PermissionError_(
        f"No consent granted for {record_type_str} records. "
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
