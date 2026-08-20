"""Audit log API endpoints for Phase 5.

View and verify tamper-evident audit logs.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.audit_log import AuditPriority
from app.models.role import RoleName
from app.models.user import User
from app.repositories import audit_log_repository
from app.schemas.response import success
from app.services import audit_service
from app.services.exceptions import NotFoundError, PermissionError_

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def list_audit_logs(
    patient_id: uuid.UUID | None = Query(None, description="Filter by patient"),
    clinician_id: uuid.UUID | None = Query(None, description="Filter by clinician"),
    action: str | None = Query(None, description="Filter by action type"),
    priority: str | None = Query(
        None,
        description="Filter by priority (normal [legacy], low, medium, high)",
    ),
    category: str | None = Query(None, description="Filter by category (auth, access, modify, consent, emergency, security, system)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """List audit logs with optional filtering.
    
    Only admins can view audit logs.
    """
    try:
        from app.models.audit_log import AuditCategory
        
        # Map priority string to enum
        priority_enum = None
        if priority:
            try:
                priority_enum = AuditPriority[priority.upper()]
            except KeyError:
                pass
        
        # Map category string to enum
        category_enum = None
        if category:
            try:
                category_enum = AuditCategory(category.lower())
            except (KeyError, ValueError):
                pass
        
        logs = audit_service.AuditService.get_audit_logs(
            db,
            user_id=clinician_id,
            patient_id=patient_id,
            action=action,
            priority=priority_enum,
            category=category_enum,
            skip=offset,
            limit=limit
        )
        
        result = []
        for log in logs:
            # Get user name if available
            user_name = None
            if log.user:
                user_name = f"{log.user.first_name} {log.user.last_name}".strip() or log.user.email
            
            # Get patient name if available
            patient_name = None
            if log.patient:
                patient_name = f"{log.patient.first_name} {log.patient.last_name}".strip()
            
            result.append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "action": log.action,
                "clinician_id": str(log.user_id) if log.user_id else None,
                "clinician_name": user_name,
                "patient_id": str(log.patient_id) if log.patient_id else None,
                "patient_name": patient_name,
                "status": log.status,
                "reason": log.reason,
                "ip_address": log.ip_address,
                "priority": log.priority.value,
                "category": log.category.value,
                "hash": log.entry_hash,
                "prev_hash": log.prev_hash
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/logs/{log_id}")
def get_audit_log(
    log_id: uuid.UUID,
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Get a specific audit log entry."""
    try:
        log = audit_log_repository.get_by_id(db, log_id)
        
        if not log:
            raise NotFoundError(f"Audit log {log_id} not found")
        
        # Get user name if available
        user_name = None
        if log.user:
            user_name = f"{log.user.first_name} {log.user.last_name}".strip() or log.user.email
        
        # Get patient name if available
        patient_name = None
        if log.patient:
            patient_name = f"{log.patient.first_name} {log.patient.last_name}".strip()
        
        return success(
            data={
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "action": log.action,
                "clinician_id": str(log.user_id) if log.user_id else None,
                "clinician_name": user_name,
                "patient_id": str(log.patient_id) if log.patient_id else None,
                "patient_name": patient_name,
                "status": log.status,
                "reason": log.reason,
                "ip_address": log.ip_address,
                "priority": log.priority.value,
                "hash": log.entry_hash,
                "prev_hash": log.prev_hash
            }
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc


@router.get("/chain-status")
def get_chain_status(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Get the status of the audit hash chain.
    
    Returns the total number of entries and the last verified hash.
    """
    try:
        status = audit_service.AuditService.get_chain_status(db)
        return success(data=status)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.post("/verify")
def verify_chain(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Verify the integrity of the entire audit hash chain.
    
    Checks that each entry's hash is correct and that the chain is unbroken.
    """
    try:
        is_valid, broken_at = audit_service.AuditService.verify_chain(db)
        
        # Get total count
        status = audit_service.AuditService.get_chain_status(db)
        total_entries = status.get("total_entries", 0)
        
        return success(
            data={
                "is_valid": is_valid,
                "total_entries": total_entries,
                "broken_at": broken_at,
                "message": "Chain is valid" if is_valid else f"Chain broken at index {broken_at}"
            }
        )
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/logs/{log_id}/verify")
def verify_single_entry(
    log_id: uuid.UUID,
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Verify a single audit log entry's hash."""
    try:
        log = audit_log_repository.get_by_id(db, log_id)
        
        if not log:
            raise NotFoundError(f"Audit log {log_id} not found")
        
        is_valid = log.verify_hash()
        
        return success(
            data={
                "log_id": str(log_id),
                "is_valid": is_valid
            }
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc


@router.get("/actions")
def list_actions(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """List all unique action types in the audit log."""
    try:
        actions = audit_log_repository.get_unique_actions(db)
        return success(data=actions)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/high-priority")
def list_high_priority(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """List high priority audit logs (break-glass, tamper detection)."""
    try:
        logs = audit_log_repository.list_high_priority(db, offset, limit)
        
        result = []
        for log in logs:
            result.append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "action": log.action,
                "clinician_id": str(log.user_id) if log.user_id else None,
                "patient_id": str(log.patient_id) if log.patient_id else None,
                "status": log.status,
                "reason": log.reason,
                "priority": log.priority.value,
                "category": log.category.value
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.post("/repair-chain")
def repair_chain(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Repair the audit hash chain.
    
    This endpoint recalculates all hashes from the beginning of the chain,
    fixing any breaks that may have occurred. This should only be used
    by admins when the chain is detected as broken.
    
    A repair action is itself logged as a high-priority security event.
    """
    try:
        # First check if chain is actually broken
        status = audit_service.AuditService.get_chain_status(db)
        
        if status.get("chain_ok"):
            return success(
                data={
                    "repaired": False,
                    "reason": "Chain is already valid, no repair needed"
                }
            )
        
        # Perform the repair
        result = audit_service.AuditService.repair_chain(db, str(current_user.id))
        
        # Commit the repair
        db.commit()
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/categories")
def list_categories(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
) -> dict:
    """List all available audit event categories."""
    from app.models.audit_log import AuditCategory
    
    categories = [
        {"value": cat.value, "name": cat.name}
        for cat in AuditCategory
    ]
    return success(data=categories)


@router.get("/priorities")
def list_priorities(
    current_user: User = Depends(require_role(RoleName.ADMIN)),
) -> dict:
    """List all available audit event priorities."""
    from app.models.audit_log import AuditPriority
    
    priorities = [
        {"value": p.value, "name": p.name}
        for p in AuditPriority
    ]
    return success(data=priorities)
