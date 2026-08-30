"""Metadata for medical files stored as objects in MinIO.

The database holds only metadata; the file bytes live in object storage.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import uuid_pk


class UploadPurpose(str, enum.Enum):
    """Purpose/category for document uploads."""
    LAB_RESULTS = "lab_results"
    PRESCRIPTIONS = "prescriptions"
    IMAGING = "imaging"
    CONSENT_FORMS = "consent_forms"
    GENERAL = "general"


class UploadedForType(str, enum.Enum):
    """Type of entity the document was uploaded for."""
    PATIENT = "patient"
    DEPARTMENT = "department"
    EXTERNAL_PROVIDER = "external_provider"
    INTERNAL_REFERENCE = "internal_reference"


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    # Optional link to a specific record this file supports.
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_records.id"), nullable=True
    )
    
    # Server-generated readable filename (stored in database)
    # Format: {patient-name}_{purpose}_{date}_{short-id}.{ext}
    # Example: john-doe_lab-results_2025-01-15_abc12345.pdf
    filename: Mapped[str] = mapped_column(String(255))
    
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    
    # Server-generated MinIO object key; never derived from the client filename.
    # Format: {patient_id}/{purpose}/{yyyy}/{mm}/{dd}/{doc_uuid}_{random}.{ext}
    storage_key: Mapped[str] = mapped_column(String(400), unique=True)
    
    # Upload tracking
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    
    # Upload purpose/category (e.g., lab_results, prescriptions)
    upload_purpose: Mapped[UploadPurpose] = mapped_column(
        SQLEnum(UploadPurpose, values_callable=lambda x: [e.value for e in x]),
        default=UploadPurpose.GENERAL,
        nullable=False
    )
    
    # Who/what the document was uploaded for (e.g., patient name, department)
    uploaded_for: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Type of entity uploaded_for represents
    uploaded_for_type: Mapped[UploadedForType | None] = mapped_column(
        SQLEnum(UploadedForType, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )

    # Document encryption metadata (for envelope encryption)
    encrypted: Mapped[bool] = mapped_column(default=False)
    nonce: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    auth_tag: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    wrapped_aes_key: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    aes_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
