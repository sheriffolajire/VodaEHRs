"""Emergency access (break-glass) API endpoints for Phase 5.

Doctors can request emergency access to bypass consent in urgent situations.
"""
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.schemas.response import success
from app.services import emergency_service
from app.services.audit_service import AuditService, AuditPriority
from app.services.exceptions import NotFoundError, PermissionError_, ValidationError

router = APIRouter(prefix="/emergency-access", tags=["emergency-access"])


class EmergencyAccessRequest(BaseModel):
    """Request for emergency access."""
    patient_id: uuid.UUID = Field(..., description="Patient to access")
    reason: str = Field(
        ..., 
        min_length=20,
        description="Mandatory reason for emergency access (min 20 chars)"
    )


class EmergencyAccessOut(BaseModel):
    """Emergency access response."""
    id: uuid.UUID
    clinician_id: uuid.UUID
    patient_id: uuid.UUID
    reason: str
    granted_at: str
    expires_at: str
    revoked_at: str | None
    is_active: bool
    remaining_minutes: float

    class Config:
        from_attributes = True


@router.post("")
def request_emergency_access(
    request: EmergencyAccessRequest,
    current_user: User = Depends(require_role(RoleName.DOCTOR)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Request emergency access (break-glass) to a patient's records.
    
    Only doctors can request emergency access. Access is granted for 30 minutes.
    A mandatory reason is required (minimum 20 characters).
    
    This creates a high-priority audit entry.
    """
    try:
        emergency = emergency_service.EmergencyService.request_emergency_access(
            db,
            current_user,
            request.patient_id,
            request.reason
        )
        
        # Audit the emergency access request
        AuditService.log_emergency_access(
            db,
            clinician_id=current_user.id,
            patient_id=request.patient_id,
            reason=request.reason
        )
        
        db.commit()
        
        # Determine message based on status
        if emergency.status == "pending":
            message = (
                f"Emergency access request submitted and pending admin approval. "
                f"Once approved, access will be valid for 30 minutes."
            )
        else:
            message = (
                f"Emergency access granted for 30 minutes. "
                f"Expires at {emergency.expires_at.isoformat()}."
            )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success(
                data={
                    "id": str(emergency.id),
                    "clinician_id": str(emergency.clinician_id),
                    "patient_id": str(emergency.patient_id),
                    "reason": emergency.reason,
                    "status": emergency.status,
                    "granted_at": emergency.granted_at.isoformat(),
                    "expires_at": emergency.expires_at.isoformat(),
                    "revoked_at": emergency.revoked_at.isoformat() if emergency.revoked_at else None,
                    "is_active": emergency.is_active(),
                    "remaining_minutes": emergency.get_remaining_minutes()
                },
                message=message
            )
        )
    except (PermissionError_, ValidationError) as exc:
        raise to_http_error(exc) from exc


@router.get("")
def list_emergency_access(
    status_filter: str | None = None,
    current_user: User = Depends(require_role(RoleName.ADMIN, RoleName.AUDITOR)),
    db: Session = Depends(get_db),
) -> dict:
    """List all emergency access requests.
    
    Only admins and auditors can view all emergency access requests.
    
    Args:
        status_filter: Filter by status (pending, approved, rejected)
    """
    try:
        # Get all emergency access (not just active)
        from app.repositories import emergency_access_repository
        emergencies = emergency_access_repository.list_all(db)
        
        # Apply status filter if provided
        if status_filter:
            emergencies = [e for e in emergencies if e.status == status_filter]
        
        result = []
        for e in emergencies:
            # Get clinician and patient names
            clinician_name = None
            patient_name = None
            if e.clinician:
                clinician_name = f"{e.clinician.first_name} {e.clinician.last_name}"
            if e.patient:
                patient_name = f"{e.patient.first_name} {e.patient.last_name}"
            
            result.append({
                "id": str(e.id),
                "clinician_id": str(e.clinician_id),
                "clinician_name": clinician_name,
                "patient_id": str(e.patient_id),
                "patient_name": patient_name,
                "reason": e.reason,
                "status": e.status,
                "granted_at": e.granted_at.isoformat(),
                "expires_at": e.expires_at.isoformat(),
                "revoked_at": e.revoked_at.isoformat() if e.revoked_at else None,
                "reviewed_at": e.reviewed_at.isoformat() if e.reviewed_at else None,
                "reviewed_by": str(e.reviewed_by) if e.reviewed_by else None,
                "review_notes": e.review_notes,
                "is_active": e.is_active(),
                "remaining_minutes": e.get_remaining_minutes()
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/my")
def my_emergency_access(
    current_user: User = Depends(require_role(RoleName.DOCTOR)),
    db: Session = Depends(get_db),
) -> dict:
    """List emergency access requests made by the current doctor."""
    try:
        # Get all active emergency access for this clinician
        emergencies = emergency_service.EmergencyService.list_active_emergency_access(
            db
        )
        # Filter to only this clinician's access
        emergencies = [e for e in emergencies if e.clinician_id == current_user.id]
        
        result = []
        for e in emergencies:
            result.append({
                "id": str(e.id),
                "clinician_id": str(e.clinician_id),
                "patient_id": str(e.patient_id),
                "reason": e.reason,
                "granted_at": e.granted_at.isoformat(),
                "expires_at": e.expires_at.isoformat(),
                "revoked_at": e.revoked_at.isoformat() if e.revoked_at else None,
                "is_active": e.is_active(),
                "remaining_minutes": e.get_remaining_minutes()
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.post("/{emergency_id}/approve")
def approve_emergency_access(
    emergency_id: uuid.UUID,
    notes: str | None = None,
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Approve an emergency access request.
    
    Only admins can approve emergency access requests.
    """
    try:
        emergency = emergency_service.EmergencyService.approve_emergency_access(
            db, current_user, emergency_id, notes
        )
        
        # Audit the approval
        AuditService.persist_audit_entry(
            db=db,
            action="emergency.approve",
            user_id=current_user.id,
            patient_id=emergency.patient_id,
            status="success",
            reason=f"Approved emergency access for clinician {emergency.clinician_id}",
            priority=AuditPriority.HIGH
        )
        
        db.commit()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success(
                data={
                    "id": str(emergency.id),
                    "status": emergency.status,
                    "reviewed_at": emergency.reviewed_at.isoformat() if emergency.reviewed_at else None,
                    "expires_at": emergency.expires_at.isoformat(),
                    "is_active": emergency.is_active()
                },
                message="Emergency access approved successfully. Access is now active for 30 minutes."
            )
        )
    except (NotFoundError, PermissionError_, ValidationError) as exc:
        raise to_http_error(exc) from exc


@router.post("/{emergency_id}/reject")
def reject_emergency_access(
    emergency_id: uuid.UUID,
    notes: str | None = None,
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Reject an emergency access request.
    
    Only admins can reject emergency access requests.
    """
    try:
        emergency = emergency_service.EmergencyService.reject_emergency_access(
            db, current_user, emergency_id, notes
        )
        
        # Audit the rejection
        AuditService.persist_audit_entry(
            db=db,
            action="emergency.reject",
            user_id=current_user.id,
            patient_id=emergency.patient_id,
            status="success",
            reason=f"Rejected emergency access for clinician {emergency.clinician_id}: {notes}",
            priority=AuditPriority.HIGH
        )
        
        db.commit()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=success(
                data={
                    "id": str(emergency.id),
                    "status": emergency.status,
                    "reviewed_at": emergency.reviewed_at.isoformat() if emergency.reviewed_at else None
                },
                message="Emergency access request rejected."
            )
        )
    except (NotFoundError, PermissionError_, ValidationError) as exc:
        raise to_http_error(exc) from exc


@router.delete("/{emergency_id}")
def revoke_emergency_access(
    emergency_id: uuid.UUID,
    current_user: User = Depends(require_role(RoleName.ADMIN)),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke an emergency access early.
    
    Only admins can revoke emergency access.
    """
    try:
        emergency = emergency_service.EmergencyService.revoke_emergency_access(
            db, current_user, emergency_id
        )
        
        # Commit the transaction to persist the revocation
        db.commit()
        
        return success(
            data={
                "id": str(emergency.id),
                "revoked_at": emergency.revoked_at.isoformat() if emergency.revoked_at else None,
                "is_active": emergency.is_active()
            },
            message="Emergency access revoked successfully."
        )
    except (NotFoundError, PermissionError_) as exc:
        db.rollback()
        raise to_http_error(exc) from exc


@router.get("/check/{patient_id}")
def check_emergency_access(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_role(RoleName.DOCTOR)),
    db: Session = Depends(get_db),
) -> dict:
    """Check if active emergency access exists for a patient.
    
    Returns the emergency access details if active, or null if not.
    """
    try:
        has_access = emergency_service.EmergencyService.has_active_emergency_access(
            db, current_user.id, patient_id
        )
        
        if has_access:
            remaining = emergency_service.EmergencyService.get_remaining_minutes(
                db, current_user.id, patient_id
            )
            return success(
                data={
                    "has_access": True,
                    "remaining_minutes": remaining
                }
            )
        
        return success(
            data={
                "has_access": False,
                "remaining_minutes": 0
            }
        )
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc
