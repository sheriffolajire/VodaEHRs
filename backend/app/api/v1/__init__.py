"""API router aggregation for API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    appointments,
    assignments,
    audit,
    auth,
    consent,
    documents,
    emergency_access,
    health,
    nursing_tasks,
    patients,
    record_versions,
    records,
    reports,
    roles,
    stats,
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
api_router.include_router(record_versions.router)
api_router.include_router(documents.router)
api_router.include_router(appointments.router)
api_router.include_router(consent.router)
api_router.include_router(emergency_access.router)
api_router.include_router(audit.router)
api_router.include_router(stats.router)
api_router.include_router(reports.router)
api_router.include_router(nursing_tasks.router)
