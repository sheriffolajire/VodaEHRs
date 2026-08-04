"""Metadata for medical files stored as objects in MinIO.

The database holds only metadata; the file bytes live in object storage.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.mixins import uuid_pk


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    # Optional link to a specific record this file supports.
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("medical_records.id"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    # Server-generated MinIO object key; never derived from the client filename.
    storage_key: Mapped[str] = mapped_column(String(400), unique=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    # Document encryption metadata (for envelope encryption)
    encrypted: Mapped[bool] = mapped_column(default=False)
    nonce: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    auth_tag: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    wrapped_aes_key: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    aes_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
