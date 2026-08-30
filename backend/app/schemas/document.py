"""Document schemas for API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.medical_document import UploadPurpose, UploadedForType


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    record_id: uuid.UUID | None
    filename: str  # Server-generated readable filename
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    uploaded_by: uuid.UUID
    
    # Upload metadata
    upload_purpose: UploadPurpose = UploadPurpose.GENERAL
    uploaded_for: str | None = None
    uploaded_for_type: UploadedForType | None = None
    
    # Encryption status for frontend display
    encrypted: bool = False
    aes_key_hash: str | None = None
    
    # Consent requirement flag - set when clinician lacks consent to view document
    requires_consent: bool = Field(
        default=False,
        description="True if the current user needs consent to view/download this document"
    )


class DocumentWithEncryptionOut(DocumentOut):
    """Document schema that includes encryption metadata for testing/admin purposes."""
    
    encrypted: bool
    nonce: str | None
    auth_tag: str | None
    wrapped_aes_key: str | None
    aes_key_hash: str | None


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload metadata."""
    
    patient_id: uuid.UUID = Field(..., description="Patient the document belongs to")
    record_id: uuid.UUID | None = Field(None, description="Optional medical record to link")
    upload_purpose: UploadPurpose = Field(
        UploadPurpose.GENERAL,
        description="Purpose/category of the upload"
    )
    uploaded_for: str | None = Field(
        None,
        description="Who/what the document was uploaded for (e.g., patient name, department)"
    )
    uploaded_for_type: UploadedForType | None = Field(
        None,
        description="Type of entity uploaded_for represents"
    )