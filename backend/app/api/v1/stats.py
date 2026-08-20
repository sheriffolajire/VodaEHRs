"""Stats API endpoints for Phase 6 dashboards.

Provides role-based statistics for dashboard displays.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.response import success
from app.services import stats_service
from app.services.exceptions import PermissionError_

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/admin")
def get_admin_stats(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Get admin dashboard statistics.
    
    Returns:
        - users_by_role: count of users per role
        - patient_count: total patients
        - record_count: total records
        - appointments_by_status: count per status
        - recent_audit_events: last 10 audit events
    """
    try:
        stats = stats_service.get_admin_stats(db)
        return success(data=stats)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/doctor")
def get_doctor_stats(
    current_user: User = Depends(require_role(RoleName.DOCTOR, RoleName.NURSE)),
    db: Session = Depends(get_db),
) -> dict:
    """Get doctor/nurse dashboard statistics.
    
    Returns:
        - assigned_patients: count of assigned patients
        - upcoming_appointments: next 5 appointments
        - recent_records: last 10 records for assigned patients
        - active_emergency_access: whether emergency access is active
    """
    try:
        stats = stats_service.get_doctor_stats(db, current_user)
        return success(data=stats)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/patient")
def get_patient_stats(
    current_user: User = Depends(require_role(RoleName.PATIENT)),
    db: Session = Depends(get_db),
) -> dict:
    """Get patient dashboard statistics.
    
    Returns:
        - record_count_by_type: count of records per type
        - upcoming_appointments: count of upcoming appointments
        - active_consents: count of active consents granted
        - document_count: count of documents
    """
    try:
        stats = stats_service.get_patient_stats(db, current_user)
        return success(data=stats)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/auditor")
def get_auditor_stats(
    current_user: User = Depends(require_role(RoleName.AUDITOR)),
    db: Session = Depends(get_db),
) -> dict:
    """Get auditor dashboard statistics.
    
    Returns:
        - events_by_action: count of audit events per action
        - break_glass_count: count of break-glass events
        - chain_ok: whether audit chain is valid
        - total_entries: total audit log entries
    """
    try:
        stats = stats_service.get_auditor_stats(db)
        return success(data=stats)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/system")
def get_system_stats(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Get system monitoring statistics.
    
    Returns:
        - db_status: database connection status
        - minio_status: MinIO connection status
        - recent_errors: recent error-level audit entries
        - counts: various entity counts
    """
    try:
        stats = stats_service.get_system_stats(db)
        return success(data=stats)
    except Exception as exc:
        # Don't expose internal errors
        return success(data={
            "db_status": "error",
            "minio_status": "error",
            "recent_errors": [],
            "counts": {},
            "error": "Failed to retrieve system stats",
        })
