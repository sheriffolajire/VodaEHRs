"""Health check endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.response import success

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return service health in the standard success envelope."""
    return success(
        data={"status": "ok", "environment": settings.environment},
        message="Service is healthy.",
    )
