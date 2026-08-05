"""Record version history model for Phase 5.

Every record update creates a new version, leaving prior versions intact.
This provides:
- Immutable audit trail of changes
- Ability to view history
- Tamper evidence (old versions can't be modified)
- Recovery from errors (can see what was changed)

Storage: Full encrypted snapshots (not diffs) for simplicity.
"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, LargeBinary, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


class RecordVersion(Base):
    """Immutable snapshot of a record at a specific version.
    
    When a record is updated:
    1. Current state is copied to a new RecordVersion row
    2. Record is updated with new content
    3. Version number is incremented
    
    This creates an append-only history that cannot be modified.
    """
    __tablename__ = "record_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    
    # Link to the record
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medical_records.id"),
        index=True,
        nullable=False
    )
    
    # Version number (sequential, starting at 1)
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Version number (1, 2, 3, ...)"
    )
    
    # Encrypted content snapshot (full snapshot, not diff)
    encrypted_data: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="AES-256-GCM encrypted content"
    )
    
    # Wrapped AES key
    encrypted_aes_key: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="RSA-OAEP wrapped AES key"
    )
    
    # AES-GCM nonce
    nonce: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="12-byte AES-GCM nonce"
    )
    
    # AES-GCM authentication tag
    auth_tag: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        comment="16-byte AES-GCM auth tag"
    )
    
    # SHA-256 hash of plaintext content
    hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of plaintext"
    )
    
    # Who created this version
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = created_at_column()
    
    # Relationships
    record: Mapped["MedicalRecord"] = relationship(
        "MedicalRecord",
        back_populates="versions",
        lazy="select"
    )
    
    creator: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    # Composite index for efficient version lookups
    __table_args__ = (
        Index('ix_record_versions_record_id_version', 'record_id', 'version'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<RecordVersion(id={self.id}, "
            f"record={self.record_id}, "
            f"version={self.version}, "
            f"created_by={self.created_by})>"
        )
