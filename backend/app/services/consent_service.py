"""Consent service for Phase 5 Zero-Trust governance.

Manages patient consent grants for clinician access to record types.
"""
import uuid
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.models.consent import Consent
from app.models.medical_record import RecordType
from app.models.user import User
from app.repositories import consent_repository
from app.services.exceptions import NotFoundError, PermissionError_


class ConsentService:
    """Service for managing patient consent."""
    
    @staticmethod
    def grant_consent(
        db: Session,
        patient: User,
        clinician_id: uuid.UUID,
        record_type: RecordType,
        expires_at: datetime | None = None
    ) -> Consent:
        """Grant consent for a clinician to access records of a specific type.
        
        Args:
            db: Database session
            patient: The patient granting consent (must be a patient user)
            clinician_id: The clinician receiving consent
            record_type: Type of records covered by this consent
            expires_at: Optional expiry date (None = never expires)
        
        Returns:
            The created Consent object
        
        Raises:
            PermissionError_: If the user is not a patient
        """
        from app.models.role import RoleName
        
        if patient.role.name != RoleName.PATIENT:
            raise PermissionError_("Only patients can grant consent.")
        
        # Check if active consent already exists
        existing = consent_repository.get_active_consent(
            db, patient.id, clinician_id, record_type
        )
        
        if existing:
            # Update expiry if consent already exists
            existing.expires_at = expires_at
            db.flush()
            db.refresh(existing)
            return existing
        
        # Create new consent
        consent = Consent(
            patient_id=patient.id,
            clinician_id=clinician_id,
            record_type=record_type.value,
            granted=True,
            expires_at=expires_at,
            revoked_at=None
        )
        
        return consent_repository.create(db, consent)
    
    @staticmethod
    def revoke_consent(
        db: Session,
        patient: User,
        consent_id: uuid.UUID
    ) -> Consent:
        """Revoke a consent.
        
        Args:
            db: Database session
            patient: The patient revoking consent
            consent_id: ID of the consent to revoke
        
        Returns:
            The revoked Consent object
        
        Raises:
            NotFoundError: If consent not found
            PermissionError_: If patient doesn't own this consent
        """
        from app.models.role import RoleName
        
        if patient.role.name != RoleName.PATIENT:
            raise PermissionError_("Only patients can revoke consent.")
        
        consent = consent_repository.revoke(db, consent_id, patient.id)
        
        if not consent:
            raise NotFoundError("Consent not found or already revoked.")
        
        return consent
    
    @staticmethod
    def list_consents(
        db: Session,
        patient: User
    ) -> list[Consent]:
        """List all consents for a patient.
        
        Args:
            db: Database session
            patient: The patient
        
        Returns:
            List of consents (active and inactive)
        """
        from app.models.role import RoleName
        
        if patient.role.name != RoleName.PATIENT:
            raise PermissionError_("Only patients can view their consents.")
        
        return consent_repository.list_for_patient(db, patient.id)
    
    @staticmethod
    def list_active_consents(
        db: Session,
        patient: User
    ) -> list[Consent]:
        """List active consents for a patient.
        
        Args:
            db: Database session
            patient: The patient
        
        Returns:
            List of active consents
        """
        from app.models.role import RoleName
        
        if patient.role.name != RoleName.PATIENT:
            raise PermissionError_("Only patients can view their consents.")
        
        return consent_repository.list_active_for_patient(db, patient.id)
    
    @staticmethod
    def check_consent(
        db: Session,
        clinician_id: uuid.UUID,
        patient_id: uuid.UUID,
        record_type: RecordType
    ) -> bool:
        """Check if active consent exists.
        
        Args:
            db: Database session
            clinician_id: The clinician requesting access
            patient_id: The patient whose records are being accessed
            record_type: Type of record being accessed
        
        Returns:
            True if active consent exists, False otherwise
        """
        return consent_repository.has_active_consent(
            db, patient_id, clinician_id, record_type
        )
