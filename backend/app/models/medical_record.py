"""Medical record model.

Content is stored as encrypted data in Phase 4. The plaintext `content` field
is replaced with encrypted fields (encrypted_data, encrypted_aes_key, nonce, auth_tag, hash).

The `signatures` relationship allows verification of record authenticity.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Enum as SQLEnum, Text
from sqlalchemy import ForeignKey, Integer, String, Text, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


class RecordType(str, enum.Enum):
    """Category of a medical record."""

    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    NURSING_NOTE = "nursing_note"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    OTHER = "other"


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    record_type: Mapped[RecordType] = mapped_column(SQLEnum(RecordType, name="record_type"))
    
    # Record metadata
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)

    # Encrypted record content (AES-256-GCM with envelope encryption)
    # Store binary data directly using LargeBinary to avoid encoding issues.
    encrypted_data: Mapped[bytes] = mapped_column(LargeBinary)
    encrypted_aes_key: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    auth_tag: Mapped[bytes] = mapped_column(LargeBinary)

    # SHA-256 hash of plaintext content for integrity verification
    hash: Mapped[str] = mapped_column(String(64))

    # NOTE: During Phase 4 the plaintext ``content`` column is still present in the
    # database schema but is no longer used by the application. It is defined as
    # ``NOT NULL`` in earlier migrations, which caused an ``IntegrityError`` when
    # inserting records without providing a value. To maintain compatibility until
    # a later migration drops the column, we map it as a nullable field with a
    # default empty string. This satisfies the database constraint without
    # re‑introducing plaintext storage.
    # Make the legacy ``content`` column optional for now. It will be dropped in a
    # later migration once all records are encrypted. Using ``nullable=True``
    # prevents the ``NOT NULL`` constraint violation during inserts.
    content: Mapped[str] = mapped_column(Text, nullable=True, server_default="", default="")

    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = created_at_column()

    # Version history (Phase 5 feature - currently always 1)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Signatures on this record
    signatures: Mapped[list["Signature"]] = relationship(
        "Signature", back_populates="record", lazy="select"
    )
