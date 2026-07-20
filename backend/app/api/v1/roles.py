"""Role listing endpoint (Admin-gated)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.role import RoleName
from app.schemas.response import success
from app.schemas.user import RoleOut
from app.services import user_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", dependencies=[Depends(require_role(RoleName.ADMIN))])
def list_roles(db: Session = Depends(get_db)) -> dict:
    roles = user_service.list_roles(db)
    return success(data=[RoleOut.model_validate(role).model_dump(mode="json") for role in roles])
