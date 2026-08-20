"""Patient-clinician assignment endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository
from app.schemas.patient import AssignmentCreate, AssignmentOut
from app.schemas.response import success
from app.services import assignment_service
from app.services.exceptions import ConflictError, NotFoundError, ValidationError

router = APIRouter(prefix="/assignments", tags=["assignments"])

_REGISTRARS = (RoleName.ADMIN, RoleName.RECEPTIONIST)


@router.post("")
def create_assignment(
    payload: AssignmentCreate,
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Assign a clinician to a patient (Admin/Receptionist)."""
    try:
        assignment = assignment_service.assign(db, payload.patient_id, payload.clinician_id, actor)
    except (NotFoundError, ConflictError, ValidationError) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=AssignmentOut.model_validate(assignment).model_dump(mode="json"),
            message="Clinician assigned.",
        ),
    )


@router.delete("/{assignment_id}")
def revoke_assignment(
    assignment_id: uuid.UUID,
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke an active assignment (Admin/Receptionist)."""
    try:
        assignment_service.revoke(db, assignment_id, actor)
    except NotFoundError as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(message="Assignment revoked.")


@router.get("")
def list_assignments(
    patient_id: uuid.UUID | None = Query(None),
    clinician_id: uuid.UUID | None = Query(None),
    active_only: bool = Query(True),
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> dict:
    """List assignments with optional filtering.
    
    - If patient_id is provided: returns assignments for that patient
    - If clinician_id is provided: returns assignments for that clinician
    - If neither: returns all assignments
    """
    if patient_id:
        assignments = assignment_repository.list_for_patient(db, patient_id, active_only)
    elif clinician_id:
        assignments = assignment_repository.list_for_clinician(db, clinician_id, active_only)
    else:
        assignments = assignment_repository.list_all(db, active_only)
    
    return success(
        data=[AssignmentOut.model_validate(a).model_dump(mode="json") for a in assignments]
    )


@router.get("/patient/{patient_id}")
def list_patient_assignments(
    patient_id: uuid.UUID,
    active_only: bool = Query(True),
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> dict:
    """List all assignments for a specific patient."""
    assignments = assignment_repository.list_for_patient(db, patient_id, active_only)
    return success(
        data=[AssignmentOut.model_validate(a).model_dump(mode="json") for a in assignments]
    )


@router.get("/clinician/{clinician_id}")
def list_clinician_assignments(
    clinician_id: uuid.UUID,
    active_only: bool = Query(True),
    actor: User = Depends(require_role(*_REGISTRARS)),
    db: Session = Depends(get_db),
) -> dict:
    """List all assignments for a specific clinician."""
    assignments = assignment_repository.list_for_clinician(db, clinician_id, active_only)
    return success(
        data=[AssignmentOut.model_validate(a).model_dump(mode="json") for a in assignments]
    )
