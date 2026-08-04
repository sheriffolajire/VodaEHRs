"""Medical record endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
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

# Clinical authors of medical records.
_AUTHORS = (RoleName.DOCTOR, RoleName.NURSE)


@router.get("")
def list_records(
    patient_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List a patient's records (access checked in the service)."""
    try:
        records = record_service.list_records(db, current_user, patient_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    records_out = []
    for record in records:
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

            records_out.append(data)
        except CryptoError:
            # Decryption failed - record exists but cannot be decrypted
            # Still return the metadata without content
            record_out = RecordOut.model_validate(record)
            data = record_out.model_dump(mode="json")
            data["content"] = None
            data["integrity_ok"] = False
            data["signed_by"] = None
            data["signature_algorithm"] = None
            data["hash"] = record.hash
            data["signatures"] = []

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