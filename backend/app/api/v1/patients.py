"""Patient endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.repositories import patient_repository
from app.schemas.patient import PatientCreate, PatientOut, PatientUpdate
from app.schemas.response import success
from app.services import patient_service
from app.services.exceptions import ConflictError, NotFoundError, PermissionError_

router = APIRouter(prefix="/patients", tags=["patients"])

# Staff who register and manage patient records.
_REGISTRARS = (RoleName.ADMIN, RoleName.RECEPTIONIST)


@router.get("/me")
def read_own_patient(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    """Return the patient record linked to the signed-in patient user (by email)."""
    if current_user.role.name != RoleName.PATIENT:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patients have a patient record.")
    patient = (
        patient_repository.get_by_email(db, current_user.email) if current_user.email else None
    )
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No patient record is linked to you.")
    return success(data=PatientOut.model_validate(patient).model_dump(mode="json"))


@router.get("")
def list_patients(
    q: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List/search patients scoped to the caller's role."""
    patients = patient_service.search_patients(db, current_user, q, limit, offset)
    db.commit()
    return success(data=[PatientOut.model_validate(p).model_dump(mode="json") for p in patients])


@router.post("")
def register_patient(
    payload: PatientCreate,
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Register a new patient (Admin/Receptionist)."""
    try:
        patient = patient_service.register_patient(db, payload, actor)
    except ConflictError as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=PatientOut.model_validate(patient).model_dump(mode="json"),
            message="Patient registered.",
        ),
    )


@router.get("/{patient_id}")
def get_patient(
    patient_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Read a patient profile the caller is authorized to view."""
    try:
        patient = patient_service.get_patient(db, current_user, patient_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(data=PatientOut.model_validate(patient).model_dump(mode="json"))


@router.patch("/{patient_id}")
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> dict:
    """Update a patient profile (Admin/Receptionist)."""
    try:
        patient = patient_service.update_patient(db, actor, patient_id, payload)
    except NotFoundError as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(
        data=PatientOut.model_validate(patient).model_dump(mode="json"),
        message="Patient updated.",
    )
