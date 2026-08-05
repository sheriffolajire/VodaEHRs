"""Emergency access (break-glass) model for Phase 5.

Break-glass allows clinicians to bypass consent in emergencies.
This is a critical security feature that must be:
- Time-limited (30 minutes)
- Justified (mandatory reason)
- Highly audited (high-priority audit entries)
- Reviewable (auditor can see all break-glass usage)
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


# Break-glass expiry duration: 30 minutes
EMERGENCY_ACCESS_DURATION_MINUTES = 30


class EmergencyAccess(Base):
    """Emergency access grant (break-glass) for bypassing consent.
    
    A clinician can request emergency access to a patient's records
    when there's an urgent medical need and consent cannot be obtained.
    
    Rules:
    - Only doctors can request (not nurses, not patients)
    - Mandatory reason required (min 20 characters)
    - Auto-expires after 30 minutes
    - Creates high-priority audit entries
    - Can be revoked early by admin
    
    Active = granted_at <= now < expires_at AND revoked_at IS NULL
    """
    __tablename__ = "emergency_access"

    id: Mapped[uuid.UUID] = uuid_pk()
    
    # Clinician requesting emergency access
    clinician_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False
    )
    
    # Patient being accessed
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
        nullable=False
    )
    
    # Mandatory justification
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Mandatory reason for emergency access (min 20 chars)"
    )
    
    # When access was granted
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now()
    )
    
    # When access expires (auto-set to granted_at + 30 minutes)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Approval workflow fields
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Status: pending, approved, rejected"
    )
    
    # Who approved/rejected the request
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="Admin who approved/rejected the request"
    )
    
    # When the request was reviewed
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the request was reviewed"
    )
    
    # Review notes (optional)
    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes from the reviewer"
    )
    
    # Early revocation tracking
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When access was revoked early"
    )
    
    # Who revoked (if early revocation)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = created_at_column()
    
    # Relationships
    clinician: Mapped["User"] = relationship(
        "User",
        foreign_keys=[clinician_id],
        back_populates="emergency_access_requests",
        lazy="select"
    )
    
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="emergency_accesses",
        lazy="select"
    )
    
    def __init__(self, **kwargs):
        """Auto-calculate expires_at if not provided."""
        if 'expires_at' not in kwargs and 'granted_at' in kwargs:
            kwargs['expires_at'] = kwargs['granted_at'] + timedelta(
                minutes=EMERGENCY_ACCESS_DURATION_MINUTES
            )
        elif 'expires_at' not in kwargs:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            kwargs['granted_at'] = now
            kwargs['expires_at'] = now + timedelta(
                minutes=EMERGENCY_ACCESS_DURATION_MINUTES
            )
        super().__init__(**kwargs)
    
    def is_active(self) -> bool:
        """Check if this emergency access is currently active.
        
        Active = approved AND not revoked AND granted_at <= now < expires_at
        """
        if self.status != "approved":
            return False
        
        if self.revoked_at is not None:
            return False
        
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        return self.granted_at <= now < self.expires_at
    
    def get_remaining_minutes(self) -> float:
        """Get remaining minutes of emergency access.
        
        Returns 0 if expired or revoked.
        """
        if not self.is_active():
            return 0.0
        
        from datetime import timezone
        now = datetime.now(timezone.utc)
        remaining = (self.expires_at - now).total_seconds() / 60
        return max(0.0, remaining)
    
    def revoke(self, revoked_by_id: uuid.UUID) -> None:
        """Revoke this emergency access early."""
        from datetime import timezone
        self.revoked_at = datetime.now(timezone.utc)
        self.revoked_by = revoked_by_id
    
    def __repr__(self) -> str:
        return (
            f"<EmergencyAccess(id={self.id}, "
            f"clinician={self.clinician_id}, "
            f"patient={self.patient_id}, "
            f"active={self.is_active()}, "
            f"remaining={self.get_remaining_minutes():.1f}min)>"
        )
