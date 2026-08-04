"""API router aggregation for API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    appointments,
    assignments,
    auth,
    documents,
    health,
    patients,
    records,
    roles,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(patients.router)
api_router.include_router(assignments.router)
api_router.include_router(records.router)
api_router.include_router(documents.router)
api_router.include_router(appointments.router)
