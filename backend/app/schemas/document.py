"""Document schemas for API responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    record_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime
    
    # Encryption status for frontend display
    encrypted: bool = False
    aes_key_hash: str | None = None


class DocumentWithEncryptionOut(DocumentOut):
    """Document schema that includes encryption metadata for testing/admin purposes."""
    
    encrypted: bool
    nonce: str | None
    auth_tag: str | None
    wrapped_aes_key: str | None
    aes_key_hash: str | None