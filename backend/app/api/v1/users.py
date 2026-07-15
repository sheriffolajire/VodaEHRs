"""User routes (scaffold).

This router demonstrates
the protected-endpoint pattern using the auth dependency placeholder.
"""

from fastapi import APIRouter, Depends

from app.api.deps import require_authenticated
from app.schemas.response import success

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", dependencies=[Depends(require_authenticated)])
def read_current_user() -> dict:
    # placeholder demonstrating the auth guard pattern.
    return success(data={"module": "users"}, message="Protected users scaffold active.")
