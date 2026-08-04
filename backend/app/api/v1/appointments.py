"""Appointment endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentUpdate
from app.schemas.response import success
from app.services import appointment_service
from app.services.exceptions import ConflictError, NotFoundError, PermissionError_

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Roles that may schedule appointments.
_SCHEDULERS = (RoleName.ADMIN, RoleName.RECEPTIONIST, RoleName.DOCTOR)


@router.get("")
def list_appointments(
    patient_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List a patient's appointments (access checked in the service)."""
    try:
        appointments = appointment_service.list_appointments(db, current_user, patient_id)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(
        data=[AppointmentOut.model_validate(a).model_dump(mode="json") for a in appointments]
    )


@router.post("")
def create_appointment(
    payload: AppointmentCreate,
    actor: User = Depends(require_role(*_SCHEDULERS)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Schedule an appointment for a patient."""
    try:
        appointment = appointment_service.create_appointment(db, actor, payload)
    except (NotFoundError, PermissionError_, ConflictError) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=AppointmentOut.model_validate(appointment).model_dump(mode="json"),
            message="Appointment scheduled.",
        ),
    )


@router.patch("/{appointment_id}")
def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    actor: User = Depends(require_role(*_SCHEDULERS)),
    db: Session = Depends(get_db),
) -> dict:
    """Reschedule, cancel, or complete an appointment."""
    try:
        appointment = appointment_service.update_appointment(db, actor, appointment_id, payload)
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc

    db.commit()
    return success(
        data=AppointmentOut.model_validate(appointment).model_dump(mode="json"),
        message="Appointment updated.",
    )
