"""Digital signatures for medical records.

This module provides the `Signature` model for storing digital signatures
on medical records, enabling verification of record authenticity and integrity.
"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


class Signature(Base):
    """Digital signature on a medical record.

    When a clinician creates a medical record, their private key is used
    to sign the record's SHA-256 hash. This signature proves:
    - Authenticity: The record was signed by the claimed clinician
    - Non-repudiation: The clinician cannot deny having created the record
    - Integrity: Any modification would invalidate the signature

    Multiple signatures can exist for a record (e.g., co-signing).
    """
    __tablename__ = "signatures"

    id: Mapped[uuid.UUID] = uuid_pk()

    # FK to medical_records.id
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medical_records.id"), index=True
    )

    # FK to users.id - the signer (authoring clinician)
    signer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    # The actual signature bytes, base64-encoded
    signature: Mapped[str] = mapped_column(Text)

    # Algorithm used: "RSA-PSS-SHA256" or "ECDSA-P256-SHA256"
    algorithm: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = created_at_column()

    # Relationships
    record: Mapped["MedicalRecord"] = relationship(
        "MedicalRecord", back_populates="signatures"
    )
    signer: Mapped["User"] = relationship("User")