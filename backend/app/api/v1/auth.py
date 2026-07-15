"""Authentication routes (scaffold).
Endpoints here define the contract shape only.
"""

from fastapi import APIRouter

from app.schemas.response import success

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status() -> dict:
    
    return success(data={"module": "auth", "ready": True}, message="Auth scaffold active.")
