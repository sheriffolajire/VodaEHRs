"""Emergency access (break-glass) repository for Phase 5.

Provides data access for emergency access grants.
"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.emergency_access import EmergencyAccess


def get_by_id(db: Session, emergency_id: uuid.UUID) -> EmergencyAccess | None:
    """Get an emergency access by ID."""
    return db.query(EmergencyAccess).filter(EmergencyAccess.id == emergency_id).first()


def get_active_for_clinician_patient(
    db: Session,
    clinician_id: uuid.UUID,
    patient_id: uuid.UUID
) -> EmergencyAccess | None:
    """Get active emergency access for a clinician/patient pair.
    
    Active = approved AND not revoked AND granted_at <= now < expires_at
    """
    now = datetime.utcnow()
    
    return db.query(EmergencyAccess).filter(
        EmergencyAccess.clinician_id == clinician_id,
        EmergencyAccess.patient_id == patient_id,
        EmergencyAccess.status == "approved",  # Must be approved by admin
        EmergencyAccess.revoked_at.is_(None),
        EmergencyAccess.granted_at <= now,
        EmergencyAccess.expires_at > now
    ).first()


def has_active_emergency_access(
    db: Session,
    clinician_id: uuid.UUID,
    patient_id: uuid.UUID
) -> bool:
    """Check if active emergency access exists."""
    return get_active_for_clinician_patient(db, clinician_id, patient_id) is not None


def list_for_patient(db: Session, patient_id: uuid.UUID) -> list[EmergencyAccess]:
    """List all emergency access requests for a patient."""
    return db.query(EmergencyAccess).filter(
        EmergencyAccess.patient_id == patient_id
    ).order_by(EmergencyAccess.created_at.desc()).all()


def list_for_clinician(db: Session, clinician_id: uuid.UUID) -> list[EmergencyAccess]:
    """List all emergency access requests by a clinician."""
    return db.query(EmergencyAccess).filter(
        EmergencyAccess.clinician_id == clinician_id
    ).order_by(EmergencyAccess.created_at.desc()).all()


def list_active(db: Session) -> list[EmergencyAccess]:
    """List all currently active emergency access grants."""
    now = datetime.utcnow()
    
    return db.query(EmergencyAccess).filter(
        EmergencyAccess.status == "approved",
        EmergencyAccess.revoked_at.is_(None),
        EmergencyAccess.granted_at <= now,
        EmergencyAccess.expires_at > now
    ).order_by(EmergencyAccess.expires_at.asc()).all()


def list_all(db: Session) -> list[EmergencyAccess]:
    """List all emergency access requests (for admin)."""
    return db.query(EmergencyAccess).order_by(
        EmergencyAccess.created_at.desc()
    ).all()


def create(db: Session, emergency_access: EmergencyAccess) -> EmergencyAccess:
    """Create a new emergency access request."""
    db.add(emergency_access)
    db.flush()
    db.refresh(emergency_access)
    return emergency_access


def revoke(
    db: Session,
    emergency_id: uuid.UUID,
    revoked_by: uuid.UUID
) -> EmergencyAccess | None:
    """Revoke an emergency access early."""
    from datetime import timezone
    
    emergency = db.query(EmergencyAccess).filter(
        EmergencyAccess.id == emergency_id
    ).first()
    
    if emergency:
        emergency.revoked_at = datetime.now(timezone.utc)
        emergency.revoked_by = revoked_by
        db.flush()
        db.refresh(emergency)
    
    return emergency
