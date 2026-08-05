"""Consent API endpoints for Phase 5.

Patients can grant/revoke consent for clinicians to access their records.
"""
import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.medical_record import RecordType
from app.models.role import RoleName
from app.models.user import User
from app.schemas.response import success
from app.services import consent_service
from app.services.audit_service import AuditService
from app.services.exceptions import NotFoundError, PermissionError_

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentGrantRequest(BaseModel):
    """Request to grant consent."""
    clinician_id: uuid.UUID = Field(..., description="Clinician to grant access to")
    record_type: RecordType = Field(..., description="Type of records covered")
    expires_at: str | None = Field(
        None, 
        description="Optional expiry date (ISO 8601 format)"
    )


class ConsentRevokeRequest(BaseModel):
    """Request to revoke consent."""
    consent_id: uuid.UUID = Field(..., description="ID of consent to revoke")


class ConsentOut(BaseModel):
    """Consent response."""
    id: uuid.UUID
    patient_id: uuid.UUID
    clinician_id: uuid.UUID
    record_type: str
    granted: bool
    expires_at: str | None
    revoked_at: str | None
    created_at: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("")
def list_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List consents for the current patient.
    
    Returns all consents (active and inactive) for the authenticated patient.
    """
    try:
        consents = consent_service.ConsentService.list_consents(
            db, current_user
        )
        
        result = []
        for c in consents:
            # Get clinician name
            clinician_name = None
            if c.clinician:
                clinician_name = f"{c.clinician.first_name} {c.clinician.last_name}".strip() or c.clinician.email
            
            result.append({
                "id": str(c.id),
                "patient_id": str(c.patient_id),
                "clinician_id": str(c.clinician_id),
                "clinician_name": clinician_name,
                "record_type": c.record_type,
                "granted": c.granted,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                "created_at": c.created_at.isoformat(),
                "is_active": c.is_active()
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.get("/active")
def list_active_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List active consents for the current patient."""
    try:
        consents = consent_service.ConsentService.list_active_consents(
            db, current_user
        )
        
        result = []
        for c in consents:
            # Get clinician name
            clinician_name = None
            if c.clinician:
                clinician_name = f"{c.clinician.first_name} {c.clinician.last_name}".strip() or c.clinician.email
            
            result.append({
                "id": str(c.id),
                "patient_id": str(c.patient_id),
                "clinician_id": str(c.clinician_id),
                "clinician_name": clinician_name,
                "record_type": c.record_type,
                "granted": c.granted,
                "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
                "created_at": c.created_at.isoformat(),
                "is_active": c.is_active()
            })
        
        return success(data=result)
    except PermissionError_ as exc:
        raise to_http_error(exc) from exc


@router.post("")
def grant_consent(
    request: ConsentGrantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Grant consent for a clinician to access records.
    
    Only patients can grant consent for their own records.
    """
    try:
        from datetime import datetime
        
        expires_at = None
        if request.expires_at:
            expires_at = datetime.fromisoformat(request.expires_at)
        
        consent = consent_service.ConsentService.grant_consent(
            db,
            current_user,
            request.clinician_id,
            request.record_type,
            expires_at
        )
        
        # Audit the consent grant
        AuditService.log_consent_grant(
            db,
            patient_id=current_user.id,
            clinician_id=request.clinician_id,
            record_type=request.record_type.value
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=success(
                data={
                    "id": str(consent.id),
                    "patient_id": str(consent.patient_id),
                    "clinician_id": str(consent.clinician_id),
                    "record_type": consent.record_type,
                    "granted": consent.granted,
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                    "created_at": consent.created_at.isoformat(),
                    "is_active": consent.is_active()
                },
                message="Consent granted successfully."
            )
        )
    except (PermissionError_, ValidationError) as exc:
        raise to_http_error(exc) from exc


@router.delete("/{consent_id}")
def revoke_consent(
    consent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Revoke a consent.
    
    Only the patient who granted the consent can revoke it.
    """
    try:
        consent = consent_service.ConsentService.revoke_consent(
            db, current_user, consent_id
        )
        
        # Audit the consent revocation
        AuditService.log_consent_revoke(
            db,
            patient_id=current_user.id,
            clinician_id=consent.clinician_id,
            record_type=consent.record_type
        )
        
        return success(
            data={
                "id": str(consent.id),
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                "is_active": consent.is_active()
            },
            message="Consent revoked successfully."
        )
    except (NotFoundError, PermissionError_) as exc:
        raise to_http_error(exc) from exc
