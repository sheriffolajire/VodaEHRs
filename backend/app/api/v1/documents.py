"""Medical document upload/download endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.document import DocumentOut, DocumentWithEncryptionOut
from app.schemas.response import success
from app.services import document_service
from app.services.exceptions import NotFoundError, PermissionError_, ValidationError

router = APIRouter(prefix="/documents", tags=["documents"])

# Clinical staff who may attach files to a patient.
_UPLOADERS = (RoleName.DOCTOR, RoleName.NURSE)


@router.get("")
def list_documents(
    patient_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List a patient's document metadata (access checked in the service)."""
    try:
        documents = document_service.list_documents(db, current_user, patient_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(data=[DocumentOut.model_validate(d).model_dump(mode="json") for d in documents])


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
    file: UploadFile = File(...),
    actor: User = Depends(require_role(*_UPLOADERS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Upload a file for an assigned patient (Doctor/Nurse)."""
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
    """Stream a document's bytes after verifying access."""
    try:
        document, stream = document_service.get_document_for_download(db, current_user, document_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return StreamingResponse(
        stream,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.filename}"'},
    )
