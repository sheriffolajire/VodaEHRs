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
from app.models.medical_document import MedicalDocument, UploadPurpose, UploadedForType
from app.models.role import RoleName
from app.models.user import User
from app.repositories import document_repository
from app.services import authorization
from app.services.audit_service import AuditService, AuditPriority
from app.services.exceptions import CryptoError, NotFoundError, PermissionError_, ValidationError
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
    upload_purpose: UploadPurpose = UploadPurpose.GENERAL,
    uploaded_for: str | None = None,
    uploaded_for_type: UploadedForType | None = None,
) -> MedicalDocument:
    """Validate, encrypt, store to MinIO, then persist metadata for a patient's file.
    
    Args:
        db: Database session
        actor: User uploading the document
        patient_id: Patient the document belongs to
        filename: Original filename (for reference only, not used in storage key)
        content_type: MIME type of the file
        size_bytes: File size in bytes
        data: File content as binary stream
        record_id: Optional medical record to link
        upload_purpose: Purpose/category of the upload
        uploaded_for: Who/what the document was uploaded for
        uploaded_for_type: Type of entity uploaded_for represents
        
    Returns:
        MedicalDocument: The created document record
    """
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

    # Fetch patient name for readable filename
    from app.repositories import patient_repository
    patient = patient_repository.get_by_id(db, patient_id)
    if patient:
        patient_name = f"{patient.first_name} {patient.last_name}".strip()
    else:
        patient_name = str(patient_id)

    # Generate server-side storage key with readable naming convention
    # Format: {patient_id}/{purpose}/{yyyy}/{mm}/{dd}/{patient-name}_{purpose}_{date}_{short-id}.{ext}
    storage_key = document_storage.build_storage_key(
        patient_id=patient_id,
        patient_name=patient_name,
        filename=filename,
        purpose=upload_purpose,
        document_id=None  # Will be updated after document creation
    )
    
    # Extract the generated filename from the storage key
    generated_filename = storage_key.split('/')[-1]
    
    document_storage.put_object(storage_key, encrypted_stream, content_type)

    document = document_repository.add(
        db,
        MedicalDocument(
            patient_id=patient_id,
            record_id=record_id,
            filename=generated_filename,  # Server-generated readable name
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            uploaded_by=actor.id,
            upload_purpose=upload_purpose,
            uploaded_for=uploaded_for,
            uploaded_for_type=uploaded_for_type,
            encrypted=True,
            nonce=nonce,
            auth_tag=auth_tag,
            wrapped_aes_key=wrapped_aes_key,
            aes_key_hash=aes_key_hash,
        ),
    )
    
    # Update storage key with document ID for traceability
    # This is optional - the key already has a UUID, but using the document ID
    # makes it easier to trace back from storage to database
    # Note: In production, you might want to regenerate and move the object
    
    record_event(
        AuditEvent(
            action="document.upload",
            user_id=str(actor.id),
            patient_id=str(patient_id),
            status="success",
            reason=f"Document ID: {document.id}, Purpose: {upload_purpose.value}, "
                   f"For: {uploaded_for or 'N/A'}, Storage: {storage_key}",
        )
    )
    return document


def list_documents(
    db: Session, 
    actor: User, 
    patient_id: uuid.UUID,
    is_admin_override: bool = False
) -> list[MedicalDocument]:
    """List a patient's document metadata after verifying access and consent.
    
    Layer 3: Resource Access (ensure_patient_access)
    Layer 4: Consent (ensure_consent) - Documents require 'document' consent
    
    Access Rules:
    - Admin: Full access to all documents
    - Patient: Full access to own documents
    - Doctor/Nurse (with consent): Full access to all documents
    - Doctor/Nurse (without consent): Can see document metadata only (no download)
    - Receptionist: NO access to documents (removed per security requirement)
    """
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, patient_id)
    
    # Receptionists should NOT have access to documents
    if actor.role.name == RoleName.RECEPTIONIST:
        raise PermissionError_("Receptionists do not have access to patient documents.")
    
    # Layer 4: Consent Check
    # Patients can always see their own documents
    if actor.role.name == RoleName.PATIENT:
        authorization.ensure_consent(
            db, actor, patient_id, 
            authorization.ResourceType.DOCUMENT,
            is_admin_override
        )
        return document_repository.list_for_patient(db, patient_id)
    
    # Admin has full access
    if actor.role.name == RoleName.ADMIN:
        return document_repository.list_for_patient(db, patient_id)
    
    # Doctor/Nurse: Check consent
    if actor.role.name in (RoleName.DOCTOR, RoleName.NURSE):
        try:
            # Has consent - return all documents with full access
            authorization.ensure_consent(
                db, actor, patient_id, 
                authorization.ResourceType.DOCUMENT,
                is_admin_override
            )
            return document_repository.list_for_patient(db, patient_id)
        except PermissionError_:
            # No consent - return documents with restricted flag
            # The frontend should show these as "requires consent to view"
            all_docs = document_repository.list_for_patient(db, patient_id)
            # Mark documents that the user didn't upload as requiring consent
            for doc in all_docs:
                if doc.uploaded_by != actor.id:
                    # Add a flag to indicate consent required
                    doc._requires_consent = True  # type: ignore
            return all_docs
    
    # Default: no access
    raise PermissionError_("Your role cannot access patient documents.")


def get_document_for_download(
    db: Session, 
    actor: User, 
    document_id: uuid.UUID,
    is_admin_override: bool = False
) -> tuple[MedicalDocument, BinaryIO]:
    """Return metadata and a decrypted stream for a document the actor may access.
    
    Layer 3: Resource Access (ensure_patient_access)
    Layer 4: Consent (ensure_consent) - Documents require 'document' consent
    Layer 5: Integrity (decrypt + verify hash)
    """
    document = document_repository.get_by_id(db, document_id)
    if document is None:
        raise NotFoundError("Document not found.")
    
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, document.patient_id)
    
    # Layer 4: Consent Check
    # Uploaders can always access their own documents
    # Patients can always access their own documents (via ensure_consent)
    # Others need explicit consent or emergency access
    has_consent = False
    if document.uploaded_by != actor.id:
        # Patients need consent check for documents they didn't upload
        # Clinicians need consent check for documents they didn't upload
        try:
            authorization.ensure_consent(
                db, actor, document.patient_id,
                authorization.ResourceType.DOCUMENT,
                is_admin_override
            )
            has_consent = True
        except PermissionError_:
            # No consent - check if they should still be allowed (for view-only)
            pass
    else:
        # Uploader always has consent for their own documents
        has_consent = True
    
    # Download permission:
    # - Document creator (uploader) can always download
    # - Patient can always download their own documents
    # - Admin with override can download
    # - Clinicians with consent can download
    can_download = (
        document.uploaded_by == actor.id or  # Uploader
        actor.role.name == RoleName.PATIENT or  # Patient owns the document
        is_admin_override or  # Admin with emergency override
        has_consent  # Clinician with patient consent
    )
    
    if not can_download:
        raise PermissionError_(
            "Only the document creator or patient can download this document. "
            "Other users have view-only access to document metadata. "
            "Use emergency override if urgent access is required."
        )
    
    # Layer 5: Integrity verification happens during decryption

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
            
            # Verify integrity (Layer 5)
            if document.aes_key_hash:
                expected_hash = base64.b64encode(hashlib.sha256(decrypted_data).digest()).decode('ascii')
                if expected_hash != document.aes_key_hash:
                    raise CryptoError("Document integrity check failed")

            # Audit log the document access (Layer 5 - Audit)
            AuditService.persist_audit_entry(
                db=db,
                action="document.view",
                user_id=actor.id,
                patient_id=document.patient_id,
                status="success",
                reason=f"Downloaded document: {document.filename}",
                priority=AuditPriority.MEDIUM
            )
            db.commit()

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