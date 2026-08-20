"""Consent repository for Phase 5 Zero-Trust governance.

Provides data access for patient consent grants.
"""
import uuid
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.consent import Consent
from app.models.medical_record import RecordType
from app.services.authorization import ResourceType


def get_by_id(db: Session, consent_id: uuid.UUID) -> Consent | None:
    """Get a consent by ID."""
    return db.query(Consent).filter(Consent.id == consent_id).first()


def get_active_consent(
    db: Session,
    patient_id: uuid.UUID,
    clinician_id: uuid.UUID,
    record_type: RecordType | ResourceType
) -> Consent | None:
    """Get active consent for a specific patient/clinician/record_type combination.
    
    Active = granted=True AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now)
    """
    now = datetime.utcnow()
    
    return db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.clinician_id == clinician_id,
        Consent.record_type == record_type.value,
        Consent.granted == True,
        Consent.revoked_at.is_(None),
        or_(
            Consent.expires_at.is_(None),
            Consent.expires_at > now
        )
    ).first()


def list_for_patient(db: Session, patient_id: uuid.UUID) -> list[Consent]:
    """List all consents for a patient (active and inactive)."""
    return db.query(Consent).filter(
        Consent.patient_id == patient_id
    ).order_by(Consent.created_at.desc()).all()


def list_active_for_patient(db: Session, patient_id: uuid.UUID) -> list[Consent]:
    """List active consents for a patient."""
    now = datetime.utcnow()
    
    return db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.granted == True,
        Consent.revoked_at.is_(None),
        or_(
            Consent.expires_at.is_(None),
            Consent.expires_at > now
        )
    ).order_by(Consent.created_at.desc()).all()


def list_for_clinician(db: Session, clinician_id: uuid.UUID) -> list[Consent]:
    """List all consents granted to a clinician."""
    return db.query(Consent).filter(
        Consent.clinician_id == clinician_id
    ).order_by(Consent.created_at.desc()).all()


def create(db: Session, consent: Consent) -> Consent:
    """Create a new consent."""
    db.add(consent)
    db.flush()
    db.refresh(consent)
    return consent


def revoke(db: Session, consent_id: uuid.UUID, patient_id: uuid.UUID) -> Consent | None:
    """Revoke a consent. Only the patient can revoke their own consents."""
    consent = db.query(Consent).filter(
        Consent.id == consent_id,
        Consent.patient_id == patient_id
    ).first()
    
    if consent:
        consent.revoked_at = datetime.utcnow()
        db.flush()
        db.refresh(consent)
    
    return consent


def has_active_consent(
    db: Session,
    patient_id: uuid.UUID,
    clinician_id: uuid.UUID,
    record_type: RecordType | ResourceType
) -> bool:
    """Check if active consent exists for patient/clinician/record_type."""
    return get_active_consent(db, patient_id, clinician_id, record_type) is not None
