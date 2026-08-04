"""Request/response schemas for medical records and documents."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.medical_record import RecordType


class RecordCreate(BaseModel):
    patient_id: uuid.UUID
    record_type: RecordType
    # Title and summary are optional for the UI; defaults are provided to avoid
    # 422 validation errors when the frontend omits them.
    title: str | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None)
    # Content is required for record creation but may be empty for certain
    # record types during testing. Enforce a minimum length of 1 when provided.
    content: str = Field(min_length=1)


class RecordSignature(BaseModel):
    """Signature information on a medical record."""
    signer_id: uuid.UUID
    algorithm: str
    created_at: datetime


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    record_type: RecordType
    title: str
    summary: str
    created_by: uuid.UUID
    created_at: datetime
    version: int

    # Phase 4: Integrity verification info
    integrity_ok: bool = True
    signed_by: uuid.UUID | None = None
    signature_algorithm: str | None = None
    
    # Additional fields for frontend display
    hash: str | None = None

    @computed_field
    @property
    def content(self) -> str | None:
        """Content field for compatibility. Returns None for encrypted records."""
        return None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    record_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
