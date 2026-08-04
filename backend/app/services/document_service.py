"""Medical document business logic: validation, storage, and metadata."""

import base64
import hashlib
import io
import uuid
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.core.config import settings
from app.crypto import keys, encryption
from app.models.medical_document import MedicalDocument
from app.models.user import User
from app.repositories import document_repository
from app.services import authorization
from app.services.exceptions import CryptoError, NotFoundError, ValidationError
from app.storage import document_storage


def _validate_upload(content_type: str, size_bytes: int) -> None:
    """Reject uploads that violate the size cap or content-type allowlist."""
    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty.")
    if size_bytes > settings.max_upload_bytes:
        raise ValidationError("File exceeds the maximum allowed size.")
    if content_type not in settings.allowed_upload_types_set:
        raise ValidationError(f"Unsupported file type: {content_type}.")


def upload_document(
    db: Session,
    actor: User,
    patient_id: uuid.UUID,
    filename: str,
    content_type: str,
    size_bytes: int,
    data: BinaryIO,
    record_id: uuid.UUID | None = None,
) -> MedicalDocument:
    """Validate, encrypt, store to MinIO, then persist metadata for a patient's file."""
    authorization.ensure_patient_access(db, actor, patient_id)
    _validate_upload(content_type, size_bytes)

    # Read file content for encryption
    file_content = data.read()
    data.seek(0)  # Reset stream for storage

    # Encrypt file content using envelope encryption
    aes_key = keys.generate_aes_key()
    encrypted_data, nonce, auth_tag = encryption.encrypt_data(file_content, aes_key)

    # Wrap AES key with institutional public key
    wrapped_aes_key = keys.wrap_aes_key_with_institutional_public(aes_key)

    # Compute hash of plaintext for integrity verification
    aes_key_hash = base64.b64encode(hashlib.sha256(file_content).digest()).decode('ascii')

    # Create encrypted content stream for storage
    encrypted_stream = io.BytesIO(encrypted_data)

    storage_key = document_storage.build_storage_key(patient_id, filename)
    document_storage.put_object(storage_key, encrypted_stream, content_type)

    document = document_repository.add(
        db,
        MedicalDocument(
            patient_id=patient_id,
            record_id=record_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            uploaded_by=actor.id,
            encrypted=True,
            nonce=nonce,
            auth_tag=auth_tag,
            wrapped_aes_key=wrapped_aes_key,
            aes_key_hash=aes_key_hash,
        ),
    )
    record_event(
        AuditEvent(
            action="document.upload",
            user_id=str(actor.id),
            patient_id=str(patient_id),
            status="success",
            reason=str(document.id),
        )
    )
    return document


def list_documents(db: Session, actor: User, patient_id: uuid.UUID) -> list[MedicalDocument]:
    """List a patient's document metadata after verifying access."""
    authorization.ensure_patient_access(db, actor, patient_id)
    return document_repository.list_for_patient(db, patient_id)


def get_document_for_download(
    db: Session, actor: User, document_id: uuid.UUID
) -> tuple[MedicalDocument, BinaryIO]:
    """Return metadata and a decrypted stream for a document the actor may access."""
    document = document_repository.get_by_id(db, document_id)
    if document is None:
        raise NotFoundError("Document not found.")
    authorization.ensure_patient_access(db, actor, document.patient_id)

    # Get encrypted data from MinIO
    encrypted_stream = document_storage.open_object_stream(document.storage_key)
    encrypted_data = encrypted_stream.read()

    # Decrypt if encrypted
    if document.encrypted and document.nonce and document.auth_tag and document.wrapped_aes_key:
        try:
            # Unwrap AES key with institutional private key
            # wrapped_aes_key is stored as LargeBinary (always bytes), no conversion needed
            aes_key = keys.unwrap_aes_key_with_institutional_private(document.wrapped_aes_key)

            # Decrypt content with AES key
            decrypted_data = encryption.decrypt_data(
                encrypted_data,
                document.nonce,
                document.auth_tag,
                aes_key
            )
            
            # Verify integrity
            if document.aes_key_hash:
                expected_hash = base64.b64encode(hashlib.sha256(decrypted_data).digest()).decode('ascii')
                if expected_hash != document.aes_key_hash:
                    raise CryptoError("Document integrity check failed")

            # Return decrypted content
            return document, io.BytesIO(decrypted_data)
        except CryptoError as e:
            # Log the specific error for debugging
            import logging
            logging.error(f"Document decryption failed for document {document_id}: {e}")
            raise CryptoError(f"Decryption failed: {e}") from e
        except Exception as e:
            # Catch any other unexpected errors
            import logging
            logging.error(f"Unexpected error during document decryption for document {document_id}: {e}")
            raise CryptoError(f"Unexpected error during decryption: {e}") from e
    else:
        # Return raw stream if not encrypted
        return document, io.BytesIO(encrypted_data)