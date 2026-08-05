"""Medical record endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.record import RecordCreate, RecordOut
from app.schemas.response import success
from app.services import record_service
from app.services.exceptions import CryptoError, NotFoundError, PermissionError_

router = APIRouter(prefix="/records", tags=["records"])


class RecordUpdate(BaseModel):
    """Update request for a medical record."""
    content: str | None = None
    title: str | None = None
    summary: str | None = None

# Clinical authors of medical records.
_AUTHORS = (RoleName.DOCTOR, RoleName.NURSE)


@router.get("")
def list_records(
    patient_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List a patient's records.
    
    Returns all records to clinicians with patient access, but only includes
    content if they have consent OR are the record creator.
    """
    from app.models.role import RoleName
    from app.services import authorization
    from app.repositories import consent_repository, emergency_access_repository
    
    try:
        # Get all records for the patient (with access check)
        records = record_service.list_records_all(db, current_user, patient_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    records_out = []
    for record in records:
        # Check if user can view content (creator OR has consent OR emergency access)
        can_view_content = False
        if current_user.role.name == RoleName.PATIENT:
            can_view_content = True  # Patient can view their own records
        elif record.created_by == current_user.id:
            can_view_content = True  # Creator can view their own records
        else:
            # Check consent or emergency access
            has_consent = consent_repository.has_active_consent(
                db, patient_id, current_user.id, record.record_type
            )
            has_emergency = emergency_access_repository.has_active_emergency_access(
                db, current_user.id, patient_id
            )
            can_view_content = has_consent or has_emergency
        
        try:
            record_out = RecordOut.model_validate(record)
            data = record_out.model_dump(mode="json")
            
            # Add creator name
            from app.repositories import user_repository
            creator = user_repository.get_by_id(db, record.created_by)
            data["created_by_name"] = f"{creator.first_name} {creator.last_name}" if creator else None
            
            if can_view_content:
                # Phase 4: Decrypt record content
                content = record_service.get_decrypted_record_content(record)
                
                # Verify record integrity
                integrity_ok, signatures = record_service.verify_record_integrity(record, content)
                
                data["content"] = content
                data["integrity_ok"] = integrity_ok
                data["signed_by"] = signatures[0].signer_id if signatures else None
                data["signature_algorithm"] = signatures[0].algorithm if signatures else None
                data["hash"] = record.hash
                data["signatures"] = [
                    {"signer_id": str(s.signer_id), "algorithm": s.algorithm, "created_at": s.created_at.isoformat()}
                    for s in signatures
                ]
                data["access_denied"] = False
            else:
                # No consent - show metadata only, hide content
                data["content"] = None
                data["integrity_ok"] = None
                data["signed_by"] = None
                data["signature_algorithm"] = None
                data["hash"] = None
                data["signatures"] = []
                data["access_denied"] = True
                data["access_denied_reason"] = "Patient consent required to view this record"

            records_out.append(data)
        except CryptoError:
            # Decryption failed - record exists but cannot be decrypted
            record_out = RecordOut.model_validate(record)
            data = record_out.model_dump(mode="json")
            data["content"] = None
            data["integrity_ok"] = False
            data["signed_by"] = None
            data["signature_algorithm"] = None
            data["hash"] = record.hash
            data["signatures"] = []
            data["access_denied"] = True
            data["access_denied_reason"] = "Unable to decrypt record"
            
            # Add creator name
            from app.repositories import user_repository
            creator = user_repository.get_by_id(db, record.created_by)
            data["created_by_name"] = f"{creator.first_name} {creator.last_name}" if creator else None

            records_out.append(data)

    db.commit()
    return success(data=records_out)


@router.post("")
def create_record(
    payload: RecordCreate,
    actor: User = Depends(require_role(*_AUTHORS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Create a medical record for an assigned patient (Doctor/Nurse)."""
    try:
        record = record_service.create_record(db, actor, payload)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=RecordOut.model_validate(record).model_dump(mode="json"),
            message="Record created.",
        ),
    )


@router.get("/{record_id}")
def get_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Read a single record after verifying access to its patient."""
    try:
        record = record_service.get_record(db, current_user, record_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    try:
        # Phase 4: Decrypt record content
        content = record_service.get_decrypted_record_content(record)

        # Verify record integrity
        integrity_ok, signatures = record_service.verify_record_integrity(record, content)

        record_out = RecordOut.model_validate(record)
        data = record_out.model_dump(mode="json")
        data["content"] = content
        data["integrity_ok"] = integrity_ok
        data["signed_by"] = signatures[0].signer_id if signatures else None
        data["signature_algorithm"] = signatures[0].algorithm if signatures else None
        data["hash"] = record.hash
        data["signatures"] = [
            {"signer_id": str(s.signer_id), "algorithm": s.algorithm, "created_at": s.created_at.isoformat()}
            for s in signatures
        ]

        db.commit()
        return success(data=data)
    except CryptoError:
        # Decryption failed
        record_out = RecordOut.model_validate(record)
        data = record_out.model_dump(mode="json")
        data["content"] = None
        data["integrity_ok"] = False
        data["signed_by"] = None
        data["signature_algorithm"] = None
        data["hash"] = record.hash
        data["signatures"] = []

        db.commit()
        return success(data=data)


@router.put("/{record_id}")
def update_record(
    record_id: uuid.UUID,
    payload: RecordUpdate,
    current_user: User = Depends(require_role(*_AUTHORS)),
    db: Session = Depends(get_db),
) -> dict:
    """Update a medical record (creates version snapshot first).
    
    Phase 5: Requires consent or break-glass access.
    """
    try:
        record = record_service.update_record(
            db,
            current_user,
            record_id,
            content=payload.content,
            title=payload.title,
            summary=payload.summary
        )
        
        db.commit()
        return success(
            data=RecordOut.model_validate(record).model_dump(mode="json"),
            message="Record updated and versioned."
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc