"""User management endpoints (Admin-gated, plus self profile)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.response import success
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service
from app.services.exceptions import ConflictError, NotFoundError, ValidationError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)) -> dict:
    """Return the authenticated user's own profile."""
    return success(data=UserOut.model_validate(current_user).model_dump(mode="json"))


@router.get(
    "/clinicians",
    dependencies=[Depends(require_role(RoleName.ADMIN, RoleName.RECEPTIONIST, RoleName.DOCTOR))],
)
def list_clinicians(db: Session = Depends(get_db)) -> dict:
    """List active doctors and nurses for assignment and scheduling."""
    clinicians = user_service.list_clinicians(db)
    return success(
        data=[UserOut.model_validate(user).model_dump(mode="json") for user in clinicians]
    )


@router.get("", dependencies=[Depends(require_role(RoleName.ADMIN))])
def list_users(db: Session = Depends(get_db)) -> dict:
    users = user_service.list_users(db)
    return success(data=[UserOut.model_validate(user).model_dump(mode="json") for user in users])


@router.post("")
def create_user(
    payload: UserCreate,
    admin: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        user = user_service.create_user(db, payload, actor_id=str(admin.id))
    except ConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=success(
            data=UserOut.model_validate(user).model_dump(mode="json"),
            message="User created.",
        ),
    )


@router.patch("/{user_id}")
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    admin: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        user = user_service.update_user(db, user_id, payload, actor_id=str(admin.id))
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    db.commit()
    return success(
        data=UserOut.model_validate(user).model_dump(mode="json"),
        message="User updated.",
    )


@router.delete("/{user_id}")
def disable_user(
    user_id: uuid.UUID,
    admin: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    try:
        user_service.disable_user(db, user_id, actor_id=str(admin.id))
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    db.commit()
    return success(message="User disabled.")
