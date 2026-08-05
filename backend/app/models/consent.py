"""Patient consent model for Phase 5 Zero-Trust governance.

Consent is the 4th layer of the Zero-Trust chain:
1. Identity (JWT token)
2. Role (require_role)
3. Resource Access (ensure_patient_access)
4. Consent (ensure_consent) ← THIS MODEL
5. Integrity (decrypt + verify)

A patient grants consent to a clinician for a specific record type.
Consent can be revoked at any time and can have an expiry.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Index
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


class ConsentStatus(str, enum.Enum):
    """Status of a consent grant."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Consent(Base):
    """Patient consent grant for clinician access to record types.
    
    A patient grants consent to a specific clinician to access records
    of a specific type (diagnosis, medication, etc.).
    
    Active consent = granted=True AND revoked_at IS NULL 
                    AND (expires_at IS NULL OR expires_at > now)
    """
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = uuid_pk()
    
    # Patient granting consent
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"), 
        index=True,
        nullable=False
    )
    
    # Clinician receiving consent
    clinician_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), 
        index=True,
        nullable=False
    )
    
    # Record type this consent applies to
    record_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of record: diagnosis, medication, nursing_note, lab_result, imaging, other"
    )
    
    # Consent status
    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="True if consent is granted, False if denied"
    )
    
    # Optional expiry date
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When consent expires (NULL = never)"
    )
    
    # Revocation tracking
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When consent was revoked"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = created_at_column()
    
    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", 
        back_populates="consents",
        lazy="select"
    )
    
    clinician: Mapped["User"] = relationship(
        "User",
        back_populates="consents_granted",
        lazy="select"
    )
    
    def is_active(self) -> bool:
        """Check if this consent is currently active.
        
        Active = granted AND not revoked AND (not expired or no expiry)
        """
        if not self.granted:
            return False
        
        if self.revoked_at is not None:
            return False
        
        if self.expires_at is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if self.expires_at <= now:
                return False
        
        return True
    
    def get_status(self) -> ConsentStatus:
        """Get the current status of this consent."""
        if self.revoked_at is not None:
            return ConsentStatus.REVOKED
        
        if self.expires_at is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if self.expires_at <= now:
                return ConsentStatus.EXPIRED
        
        if self.granted:
            return ConsentStatus.ACTIVE
        
        return ConsentStatus.REVOKED
    
    def __repr__(self) -> str:
        return (
            f"<Consent(id={self.id}, "
            f"patient={self.patient_id}, "
            f"clinician={self.clinician_id}, "
            f"type={self.record_type}, "
            f"active={self.is_active()})>"
        )
