"""Medical document upload/download endpoints."""

import uuid
from unicodedata import normalize
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.medical_document import UploadPurpose, UploadedForType
from app.models.role import RoleName
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentWithEncryptionOut
from app.schemas.response import success
from app.services import document_service
from app.services.exceptions import NotFoundError, PermissionError_, ValidationError

router = APIRouter(prefix="/documents", tags=["documents"])

# Clinical staff who may attach files to a patient.
_UPLOADERS = (RoleName.DOCTOR, RoleName.NURSE)


def _attachment_content_disposition(filename: str) -> str:
    """Return an RFC 5987-compatible attachment header for any filename.

    Response headers must be Latin-1, but uploaded filenames can contain any
    Unicode character. Supply a safe ASCII fallback for older clients and an
    encoded UTF-8 ``filename*`` value for clients that support it.
    """
    safe_filename = filename.replace("\r", "").replace("\n", "") or "download"
    ascii_filename = normalize("NFKD", safe_filename).encode("ascii", "ignore").decode("ascii")
    ascii_filename = ascii_filename.replace("\\", "_").replace('"', "'")
    ascii_filename = "".join(
        character if 32 <= ord(character) <= 126 else "_"
        for character in ascii_filename
    ) or "download"

    return (
        f'attachment; filename="{ascii_filename}"; '
        f"filename*=UTF-8''{quote(safe_filename, safe='')}"
    )


@router.get("")
def list_documents(
    patient_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List a patient's document metadata (access checked in the service).
    
    Emergency override: If the user has active emergency access for this patient,
    they can view all documents (not just their own uploads).
    
    For clinicians without consent: Documents are returned with requires_consent=True
    to indicate they need patient consent to view/download.
    """
    from app.repositories import emergency_access_repository
    from app.models.role import RoleName
    
    # Block receptionists from accessing documents
    if current_user.role.name == RoleName.RECEPTIONIST:
        raise to_http_error(PermissionError_("Receptionists do not have access to patient documents."))
    
    # Check for emergency access (break-glass override)
    has_emergency = emergency_access_repository.has_active_emergency_access(
        db, current_user.id, patient_id
    )
    
    try:
        documents = document_service.list_documents(
            db, current_user, patient_id, is_admin_override=has_emergency
        )
        
        # Determine if user has full consent for documents
        has_full_consent = (
            current_user.role.name == RoleName.ADMIN or
            current_user.role.name == RoleName.PATIENT or
            has_emergency
        )
        
        if not has_full_consent and current_user.role.name in (RoleName.DOCTOR, RoleName.NURSE):
            # Check if clinician has explicit consent
            try:
                from app.services import authorization
                authorization.ensure_consent(
                    db, current_user, patient_id, 
                    authorization.ResourceType.DOCUMENT,
                    has_emergency
                )
                has_full_consent = True
            except PermissionError_:
                has_full_consent = False
        
        # Build response with consent flags
        result = []
        for doc in documents:
            doc_dict = DocumentOut.model_validate(doc).model_dump()
            # Set requires_consent flag
            if not has_full_consent and doc.uploaded_by != current_user.id:
                doc_dict["requires_consent"] = True
            result.append(doc_dict)
        
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(data=result)


@router.get("/{document_id}/details")
def get_document_details(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get detailed document metadata including encryption info (admin/technical use)."""
    from app.models.medical_document import MedicalDocument
    from app.models.role import RoleName
    
    # Only admins can access detailed encryption metadata
    if current_user.role.name != RoleName.ADMIN:
        raise to_http_error(PermissionError_("Only administrators can access document details"))
    
    try:
        document = db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        if document is None:
            raise to_http_error(NotFoundError("Document not found"))
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    
    # Manually construct the response dict with proper base64 encoding
    import base64
    
    doc_dict = {
        "id": document.id,
        "patient_id": document.patient_id,
        "record_id": document.record_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "uploaded_at": document.uploaded_at,
        "encrypted": document.encrypted,
        "nonce": base64.b64encode(document.nonce).decode('utf-8') if document.nonce else None,
        "auth_tag": base64.b64encode(document.auth_tag).decode('utf-8') if document.auth_tag else None,
        "wrapped_aes_key": base64.b64encode(document.wrapped_aes_key).decode('utf-8') if document.wrapped_aes_key else None,
        "aes_key_hash": document.aes_key_hash
    }
    
    return success(data=doc_dict)


@router.post("")
def upload_document(
    patient_id: uuid.UUID = Form(...),
    record_id: uuid.UUID | None = Form(default=None),
    upload_purpose: str = Form(default="general"),
    uploaded_for: str | None = Form(default=None, max_length=255),
    uploaded_for_type: str | None = Form(default=None),
    file: UploadFile = File(...),
    actor: User = Depends(require_role(*_UPLOADERS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Upload a file for an assigned patient (Doctor/Nurse).
    
    Args:
        patient_id: Patient the document belongs to
        record_id: Optional medical record to link
        upload_purpose: Purpose/category of the upload (lab_results, prescriptions, etc.)
        uploaded_for: Who/what the document was uploaded for (e.g., patient name, department)
        uploaded_for_type: Type of entity uploaded_for represents
        file: The file to upload
    """
    # Convert string values to enums (handle both uppercase names and lowercase values)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Raw upload_purpose from form: {upload_purpose!r}")
    logger.info(f"Raw uploaded_for_type from form: {uploaded_for_type!r}")
    
    # Map both lowercase values and uppercase names to enum members
    purpose_map = {
        # Lowercase values (correct format for DB)
        "lab_results": UploadPurpose.LAB_RESULTS,
        "prescriptions": UploadPurpose.PRESCRIPTIONS,
        "imaging": UploadPurpose.IMAGING,
        "consent_forms": UploadPurpose.CONSENT_FORMS,
        "general": UploadPurpose.GENERAL,
        # Uppercase names (what frontend sometimes sends)
        "LAB_RESULTS": UploadPurpose.LAB_RESULTS,
        "PRESCRIPTIONS": UploadPurpose.PRESCRIPTIONS,
        "IMAGING": UploadPurpose.IMAGING,
        "CONSENT_FORMS": UploadPurpose.CONSENT_FORMS,
        "GENERAL": UploadPurpose.GENERAL,
    }
    
    # Try direct lookup first, then lowercase lookup
    purpose_enum = purpose_map.get(upload_purpose)
    if purpose_enum is None:
        purpose_enum = purpose_map.get(upload_purpose.lower(), UploadPurpose.GENERAL)
    
    logger.info(f"Converted upload_purpose to enum: {purpose_enum}")
    
    uploaded_for_type_enum = None
    if uploaded_for_type:
        type_map = {
            "patient": UploadedForType.PATIENT,
            "department": UploadedForType.DEPARTMENT,
            "external_provider": UploadedForType.EXTERNAL_PROVIDER,
            "internal_reference": UploadedForType.INTERNAL_REFERENCE,
            "PATIENT": UploadedForType.PATIENT,
            "DEPARTMENT": UploadedForType.DEPARTMENT,
            "EXTERNAL_PROVIDER": UploadedForType.EXTERNAL_PROVIDER,
            "INTERNAL_REFERENCE": UploadedForType.INTERNAL_REFERENCE,
        }
        uploaded_for_type_enum = type_map.get(uploaded_for_type)
        if uploaded_for_type_enum is None:
            uploaded_for_type_enum = type_map.get(uploaded_for_type.lower())
        logger.info(f"Converted uploaded_for_type to enum: {uploaded_for_type_enum}")
    
    # Read into memory to size it; Phase 3 files are capped well below RAM limits.
    contents = file.file.read()
    file.file.seek(0)
    try:
        document = document_service.upload_document(
            db,
            actor,
            patient_id,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(contents),
            data=file.file,
            record_id=record_id,
            upload_purpose=purpose_enum,
            uploaded_for=uploaded_for,
            uploaded_for_type=uploaded_for_type_enum,
        )
    except (NotFoundError, PermissionError_, ValidationError) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=DocumentOut.model_validate(document).model_dump(mode="json"),
            message="Document uploaded.",
        ),
    )


@router.get("/{document_id}")
def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream a document's bytes after verifying access.
    
    Emergency override: If the user has active emergency access for this patient,
    they can download the document even if they are not the creator.
    
    Clinicians without consent cannot download documents they didn't upload.
    """
    from app.repositories import document_repository, emergency_access_repository
    from app.models.role import RoleName
    from app.services import authorization
    from app.services.exceptions import PermissionError_
    
    # Block receptionists from downloading documents
    if current_user.role.name == RoleName.RECEPTIONIST:
        raise to_http_error(PermissionError_("Receptionists do not have access to patient documents."))
    
    # First get the document to find the patient_id
    document = document_repository.get_by_id(db, document_id)
    if document is None:
        raise to_http_error(NotFoundError("Document not found"))
    
    # Check for emergency access (break-glass override)
    has_emergency = emergency_access_repository.has_active_emergency_access(
        db, current_user.id, document.patient_id
    )
    
    # For doctors/nurses without emergency access, check if they have consent
    # or are the document uploader
    if (current_user.role.name in (RoleName.DOCTOR, RoleName.NURSE) and 
        not has_emergency and 
        document.uploaded_by != current_user.id):
        try:
            authorization.ensure_consent(
                db, current_user, document.patient_id,
                authorization.ResourceType.DOCUMENT
            )
        except PermissionError_:
            raise to_http_error(PermissionError_(
                "You need patient consent to download this document. "
                "You can only download documents you uploaded or request consent from the patient."
            ))
    
    try:
        document, stream = document_service.get_document_for_download(
            db, current_user, document_id, is_admin_override=has_emergency
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return StreamingResponse(
        stream,
        media_type=document.content_type,
        headers={"Content-Disposition": _attachment_content_disposition(document.filename)},
    )


@router.post("/{document_id}/admin-override")
def admin_override_download(
    document_id: uuid.UUID,
    reason: str = Form(..., min_length=20),
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Admin override to download a document without being the creator.
    
    Only admins can use this endpoint. The admin must provide a reason
    (minimum 20 characters) for the override, which is logged for audit.
    """
    from app.repositories import document_repository
    from app.services.audit_service import AuditService, AuditPriority
    
    # Get the document
    document = document_repository.get_by_id(db, document_id)
    if document is None:
        raise to_http_error(NotFoundError("Document not found"))
    
    # Log the admin override for audit
    AuditService.persist_audit_entry(
        db=db,
        action="document.admin_override",
        user_id=current_user.id,
        patient_id=document.patient_id,
        status="success",
        reason=f"Admin override download: {document.filename}. Reason: {reason}",
        priority=AuditPriority.HIGH
    )
    
    try:
        # Pass is_admin_override=True to allow download
        document, stream = document_service.get_document_for_download(
            db, current_user, document_id, is_admin_override=True
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return StreamingResponse(
        stream,
        media_type=document.content_type,
        headers={"Content-Disposition": _attachment_content_disposition(document.filename)},
    )
