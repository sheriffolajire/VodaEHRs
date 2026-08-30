"""Stats service for Phase 6 dashboards.

Provides role-based statistics and aggregations for dashboards.
All stats respect existing access control rules.
"""

import uuid
from datetime import datetime, timedelta, UTC
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.appointment import Appointment, AppointmentStatus
from app.models.consent import Consent
from app.models.medical_document import MedicalDocument
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.role import RoleName
from app.models.user import User
from app.repositories import assignment_repository, audit_log_repository
from app.services.exceptions import PermissionError_

logger = get_logger("stats_service")


def get_admin_stats(db: Session) -> dict[str, Any]:
    """Get admin dashboard statistics.
    
    Returns:
        - users_by_role: count of users per role
        - patient_count: total patients
        - record_count: total records
        - appointments_by_status: count per status
        - recent_audit_events: last 10 audit events
    """
    # Users by role
    users_by_role = {}
    for role in RoleName:
        count = db.query(User).filter(User.role.has(name=role)).count()
        users_by_role[role] = count
    
    # Patient count
    patient_count = db.query(Patient).count()
    
    # Record count
    record_count = db.query(MedicalRecord).count()
    
    # Appointments by status
    appointments_by_status = {}
    for status in AppointmentStatus:
        count = db.query(Appointment).filter(Appointment.status == status).count()
        appointments_by_status[status.value] = count
    
    # Recent audit events (last 10)
    recent_audit = audit_log_repository.get_recent_entries(db, limit=10)
    recent_audit_events = [
        {
            "id": str(entry.id),
            "action": entry.action,
            "user_id": str(entry.user_id) if entry.user_id else None,
            "status": entry.status,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in recent_audit
    ]
    
    return {
        "users_by_role": users_by_role,
        "patient_count": patient_count,
        "record_count": record_count,
        "appointments_by_status": appointments_by_status,
        "recent_audit_events": recent_audit_events,
    }


def get_doctor_stats(db: Session, doctor: User) -> dict[str, Any]:
    """Get doctor/nurse dashboard statistics.
    
    Returns:
        - assigned_patients: count of assigned patients
        - upcoming_appointments: next 5 appointments
        - recent_records: last 10 records for assigned patients
        - active_emergency_access: whether emergency access is active
    """
    # Get assigned patient IDs
    assigned_patient_ids = assignment_repository.list_patient_ids_for_clinician(db, doctor.id)
    
    # Upcoming appointments (next 5)
    now = datetime.now(UTC)
    upcoming = (
        db.query(Appointment, Patient)
        .join(Patient, Patient.id == Appointment.patient_id)
        .filter(
            Appointment.clinician_id == doctor.id,
            Appointment.scheduled_at >= now,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
        .order_by(Appointment.scheduled_at.asc())
        .limit(5)
        .all()
    )
    
    upcoming_appointments = [
        {
            "id": str(a.id),
            "patient_id": str(a.patient_id),
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "scheduled_at": a.scheduled_at.isoformat(),
            "reason": a.reason,
        }
        for a, patient in upcoming
    ]
    
    # Recent records for assigned patients (last 10)
    recent_records = []
    if assigned_patient_ids:
        records = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id.in_(assigned_patient_ids))
            .order_by(MedicalRecord.created_at.desc())
            .limit(10)
            .all()
        )
        recent_records = [
            {
                "id": str(r.id),
                "patient_id": str(r.patient_id),
                "record_type": r.record_type.value,
                "created_at": r.created_at.isoformat(),
                "created_by": str(r.created_by),
            }
            for r in records
        ]
    
    # Check active emergency access
    from app.repositories import emergency_access_repository
    
    # Check if clinician has any active emergency access
    emergency_access_list = emergency_access_repository.list_for_clinician(db, doctor.id)
    now = datetime.now(UTC)
    has_emergency = any(
        ea.revoked_at is None and ea.granted_at <= now < ea.expires_at
        for ea in emergency_access_list
    )
    
    return {
        "assigned_patients": len(assigned_patient_ids),
        "upcoming_appointments": upcoming_appointments,
        "recent_records": recent_records,
        "active_emergency_access": has_emergency,
    }


def get_patient_stats(db: Session, patient: User) -> dict[str, Any]:
    """Get patient dashboard statistics.
    
    Returns:
        - record_count_by_type: count of records per type
        - upcoming_appointments: count of upcoming appointments
        - active_consents: count of active consents granted
        - document_count: count of documents
    """
    # Get patient record - try by email first, then by name match
    patient_record = db.query(Patient).filter(Patient.email == patient.email).first()
    
    # If not found by email, try matching by first_name + last_name
    if not patient_record and patient.first_name and patient.last_name:
        patient_record = (
            db.query(Patient)
            .filter(
                Patient.first_name == patient.first_name,
                Patient.last_name == patient.last_name,
            )
            .first()
        )
    
    if not patient_record:
        logger.warning(f"No patient record found for user {patient.email} ({patient.first_name} {patient.last_name})")
        return {
            "record_count_by_type": {},
            "upcoming_appointments": 0,
            "active_consents": 0,
            "document_count": 0,
        }
    
    patient_id = patient_record.id
    
    # Records by type
    from app.models.medical_record import RecordType
    record_count_by_type = {}
    for rt in RecordType:
        count = (
            db.query(MedicalRecord)
            .filter(
                MedicalRecord.patient_id == patient_id,
                MedicalRecord.record_type == rt,
            )
            .count()
        )
        record_count_by_type[rt.value] = count
    
    # Upcoming appointments
    now = datetime.now(UTC)
    upcoming_appointments = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.scheduled_at >= now,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
        .count()
    )
    
    # Active consents (granted to clinicians)
    active_consents = (
        db.query(Consent)
        .filter(
            Consent.patient_id == patient_id,
            Consent.granted == True,
            Consent.revoked_at.is_(None),
        )
        .count()
    )
    
    # Document count
    from app.models.medical_document import MedicalDocument
    document_count = (
        db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == patient_id)
        .count()
    )
    
    return {
        "patient_id": str(patient_id),
        "record_count_by_type": record_count_by_type,
        "upcoming_appointments": upcoming_appointments,
        "active_consents": active_consents,
        "document_count": document_count,
    }


def get_auditor_stats(db: Session) -> dict[str, Any]:
    """Get auditor dashboard statistics.
    
    Returns:
        - events_by_action: count of audit events per action
        - break_glass_count: count of break-glass events
        - chain_ok: whether audit chain is valid
        - total_entries: total audit log entries
    """
    # Events by action (last 30 days)
    thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
    
    from app.models.audit_log import AuditLog
    events_by_action = {}
    actions = db.query(AuditLog.action).distinct().all()
    for (action,) in actions:
        if action:
            count = (
                db.query(AuditLog)
                .filter(
                    AuditLog.action == action,
                    AuditLog.created_at >= thirty_days_ago,
                )
                .count()
            )
            events_by_action[action] = count
    
    # Break-glass events (last 30 days)
    break_glass_count = (
        db.query(AuditLog)
        .filter(
            AuditLog.action.like("emergency.%"),
            AuditLog.created_at >= thirty_days_ago,
        )
        .count()
    )
    
    # Chain integrity
    chain_status = audit_log_repository.get_chain_status(db)
    
    return {
        "events_by_action": events_by_action,
        "break_glass_count": break_glass_count,
        "chain_ok": chain_status["chain_ok"],
        "total_entries": chain_status["total_entries"],
        "last_entry_time": chain_status["last_entry_time"],
    }


def get_system_stats(db: Session) -> dict[str, Any]:
    """Get system monitoring statistics.
    
    Returns:
        - db_status: database connection status
        - minio_status: MinIO connection status
        - recent_errors: recent error-level audit entries
        - counts: various entity counts
        - database: detailed database metrics
        - storage: storage usage metrics
        - uptime_hours: approximate uptime
    """
    import time
    from sqlalchemy import text
    
    # Database status with latency check
    db_connected = False
    db_latency_ms = 0
    try:
        start_time = time.time()
        db.execute(text("SELECT 1"))
        db_latency_ms = (time.time() - start_time) * 1000
        db_connected = True
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    # MinIO status with bucket info
    minio_connected = False
    bucket_count = 0
    try:
        from app.storage.minio_client import get_storage_client
        from app.core.config import settings
        minio_client = get_storage_client()
        buckets = minio_client.list_buckets()
        bucket_count = len(buckets)
        minio_connected = True
        minio_status = "ok"
    except Exception as e:
        minio_status = "error"
        logger.warning(f"MinIO connection failed: {e}")
    
    # Recent errors (last 10)
    from app.models.audit_log import AuditLog
    recent_errors = (
        db.query(AuditLog)
        .filter(AuditLog.status == "error")
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    
    recent_errors_list = [
        {
            "id": str(e.id),
            "action": e.action,
            "reason": e.reason or "Unknown error",
            "created_at": e.created_at.isoformat(),
        }
        for e in recent_errors
    ]
    
    # Entity counts
    counts = {
        "users": db.query(User).count(),
        "patients": db.query(Patient).count(),
        "records": db.query(MedicalRecord).count(),
        "appointments": db.query(Appointment).count(),
        "documents": db.query(MedicalDocument).count(),
    }
    
    # Database metrics
    active_connections = 0
    db_uptime_hours = 0
    try:
        # PostgreSQL specific - get active connections
        result = db.execute(text(
            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
        ))
        active_connections = result.scalar() or 0
        
        # Get database uptime from PostgreSQL
        result = db.execute(text(
            "SELECT EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time())) / 3600 as uptime_hours"
        ))
        db_uptime_hours = round(result.scalar() or 0, 2)
    except Exception:
        pass
    
    database_metrics = {
        "connected": db_connected,
        "latency_ms": round(db_latency_ms, 2),
        "active_connections": active_connections,
        "uptime_hours": db_uptime_hours,
    }
    
    # Storage metrics (actual from MinIO)
    actual_used_bytes = 0
    if minio_connected:
        try:
            from app.storage.document_storage import get_bucket_size
            actual_used_bytes = get_bucket_size()
        except Exception:
            pass
    
    storage_metrics = {
        "healthy": minio_connected,
        "used_bytes": actual_used_bytes,
        "total_bytes": 10 * 1024 * 1024 * 1024,  # 10GB quota
        "buckets": bucket_count,
    }
    
    return {
        "db_status": db_status,
        "minio_status": minio_status,
        "recent_errors": recent_errors_list,
        "counts": counts,
        "database": database_metrics,
        "storage": storage_metrics,
        "uptime_hours": db_uptime_hours,
    }
