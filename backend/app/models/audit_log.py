"""Immutable audit log model with hash chaining for Phase 5.

Audit logs are append-only and form a hash chain for tamper evidence.
Each entry includes the hash of the previous entry, creating a chain
that would break if any entry were modified or deleted.

Hash chain formula:
    entry_hash = SHA256(prev_hash + action + user_id + patient_id + 
                        status + timestamp + ...)

This provides:
- Tamper evidence (chain break is detectable)
- Immutable history (no deletes, no updates)
- Compliance (audit trail for regulations)
- Forensics (investigate security incidents)
"""
import enum
import uuid
import hashlib
import json
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import uuid_pk


class AuditPriority(str, enum.Enum):
    """Priority level for audit entries.

    ``NORMAL`` is retained only to read audit entries created before the
    LOW/MEDIUM split. Its value is part of the immutable audit hash, so old
    entries must not be reinterpreted as a different priority.
    """

    NORMAL = "normal"
    LOW = "low"  # Routine operations, views
    MEDIUM = "medium"  # Data modifications, access grants
    HIGH = "high"  # Break-glass, tamper detection, security events


class AuditCategory(str, enum.Enum):
    """Category for audit entries."""
    AUTH = "auth"           # Authentication events
    ACCESS = "access"       # Data access (view, read)
    MODIFY = "modify"       # Data modifications (create, update, delete)
    CONSENT = "consent"     # Consent management
    EMERGENCY = "emergency" # Emergency access
    SECURITY = "security"   # Security events (tamper, violations)
    SYSTEM = "system"       # System events (backup, maintenance)


class AuditLog(Base):
    """Immutable audit log entry with hash chaining.
    
    Each entry contains:
    - Event details (action, user, patient, status)
    - Hash of previous entry (chain link)
    - Hash of this entry (for verification)
    - Priority (normal or high)
    
    The hash chain provides tamper evidence:
    - If any entry is modified, its hash changes
    - This breaks the chain (next entry's prev_hash won't match)
    - Verification detects the break
    
    Entries are append-only:
    - Never update existing entries
    - Never delete entries
    - Only insert new entries
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    
    # Who performed the action (nullable for system events)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    # Which patient was affected (nullable for non-patient actions)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("patients.id"),
        nullable=True,
        index=True
    )
    
    # What action was performed
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action: record.view, consent.grant, emergency.access, etc."
    )
    
    # Action status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="success, failure, tamper_detected"
    )
    
    # Optional reason/details
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional context (e.g., break-glass reason)"
    )
    
    # IP address (for forensics)
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True
    )
    
    # Priority (low, medium, high)
    priority: Mapped[AuditPriority] = mapped_column(
        SQLEnum(AuditPriority),
        default=AuditPriority.LOW,
        nullable=False,
        index=True
    )
    
    # Category for grouping events
    category: Mapped[AuditCategory] = mapped_column(
        SQLEnum(AuditCategory),
        default=AuditCategory.ACCESS,
        nullable=False,
        index=True
    )
    
    # Hash chain: hash of previous entry
    prev_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of previous audit entry (NULL for first entry)"
    )
    
    # Hash chain: hash of this entry
    entry_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hash of this entry (includes prev_hash)"
    )
    
    # Timestamp (when event occurred)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now()
    )
    
    # Relationships
    user: Mapped["User | None"] = relationship(
        "User",
        lazy="select"
    )
    
    patient: Mapped["Patient | None"] = relationship(
        "Patient",
        lazy="select"
    )
    
    # Index for efficient querying
    __table_args__ = (
        Index('ix_audit_logs_created_at', 'created_at'),
        Index('ix_audit_logs_action_created', 'action', 'created_at'),
    )
    
    def compute_hash(self) -> str:
        """Compute the hash of this entry.
        
        The hash includes:
        - prev_hash (chain link)
        - action
        - user_id
        - patient_id
        - status
        - reason (if present)
        - created_at (ISO format)
        - priority
        
        This creates a chain where each entry depends on the previous.
        """
        data = {
            "prev_hash": self.prev_hash or "",
            "action": self.action,
            "user_id": str(self.user_id) if self.user_id else "",
            "patient_id": str(self.patient_id) if self.patient_id else "",
            "status": self.status,
            "reason": self.reason or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "priority": self.priority.value if self.priority else "normal"
        }
        
        # Canonical JSON representation
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def verify_hash(self) -> bool:
        """Verify that entry_hash matches computed hash.
        
        Returns True if hash is valid, False if tampered.
        """
        computed = self.compute_hash()
        return computed == self.entry_hash
    
    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, "
            f"action={self.action}, "
            f"user={self.user_id}, "
            f"patient={self.patient_id}, "
            f"priority={self.priority.value}, "
            f"created={self.created_at})>"
        )
