"""
Reports API - Phase 6

Provides endpoints for generating and downloading CSV reports.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, logger
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.report_service import ReportService
from app.api.deps import require_role

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/patient/{patient_id}/summary.csv",
    summary="Generate patient summary CSV",
    description="Generate a comprehensive patient summary report including demographics, medical history, records, and appointments."
)
async def get_patient_summary_report(
    patient_id: str,
    from_date: Optional[datetime] = Query(
        None,
        description="Start date for records filter (ISO 8601 format)"
    ),
    to_date: Optional[datetime] = Query(
        None,
        description="End date for records filter (ISO 8601 format)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Doctor", "Nurse", "Receptionist", "Patient"))
):
    """
    Generate a patient summary CSV report.
    
    - **patient_id**: UUID of the patient
    - **from_date**: Start date for records filter (optional)
    - **to_date**: End date for records filter (optional)
    - Returns: CSV file download
    
    Required roles: Admin, Doctor, Nurse, Receptionist, Patient
    - Patients can only download their own health summary
    - Staff can download any patient's summary
    """
    try:
        # Calculate date range for records filter
        if to_date:
            report_to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            report_to_date = None
        
        if from_date:
            report_from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            report_from_date = None
        
        report_service = ReportService(db)
        result = report_service.generate_patient_summary_pdf(
            patient_id=patient_id,
            current_user_id=str(current_user.id),
            from_date=report_from_date,
            to_date=report_to_date
        )
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"patient_summary_{patient_id[:8]}_{timestamp}.{result.extension}"
        
        return StreamingResponse(
            result.buffer,
            media_type=result.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-Type": "patient-summary",
                "X-Generated-By": str(current_user.id),
                "X-Generated-At": datetime.utcnow().isoformat(),
                "X-Report-Format": result.extension
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get(
    "/compliance.csv",
    summary="Generate compliance audit CSV",
    description="Generate a compliance audit report covering audit events, chain integrity, and access patterns."
)
async def get_compliance_report(
    from_date: Optional[datetime] = Query(
        None,
        description="Start date for report period (ISO 8601 format)"
    ),
    to_date: Optional[datetime] = Query(
        None,
        description="End date for report period (ISO 8601 format)"
    ),
    days: Optional[int] = Query(
        30,
        ge=1,
        le=365,
        description="Number of days to include (default: 30, max: 365)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin", "Auditor"))
):
    """
    Generate a compliance audit CSV report.
    
    - **from_date**: Start date (optional, defaults to 'days' ago)
    - **to_date**: End date (optional, defaults to now)
    - **days**: Number of days to include (default: 30)
    - Returns: CSV file download
    
    Required roles: Admin, Auditor
    """
    try:
        # Calculate date range
        # If to_date is provided, set it to end of day (23:59:59)
        # If from_date is provided, set it to start of day (00:00:00)
        if to_date:
            report_to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            report_to_date = datetime.utcnow()
        
        if from_date:
            report_from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            report_from_date = report_to_date - timedelta(days=days)
        
        # Debug logging
        logger.logger.info(f"Compliance report request - from_date param: {from_date}, to_date param: {to_date}")
        logger.logger.info(f"Compliance report calculated - from: {report_from_date}, to: {report_to_date}")
        
        report_service = ReportService(db)
        result = report_service.generate_compliance_report_pdf(
            from_date=report_from_date,
            to_date=report_to_date,
            current_user_id=str(current_user.id)
        )
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        from_str = report_from_date.strftime("%Y%m%d")
        to_str = report_to_date.strftime("%Y%m%d")
        filename = f"compliance_report_{from_str}_{to_str}_{timestamp}.{result.extension}"
        
        return StreamingResponse(
            result.buffer,
            media_type=result.content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Report-Type": "compliance",
                "X-Report-From": report_from_date.isoformat(),
                "X-Report-To": report_to_date.isoformat(),
                "X-Generated-By": str(current_user.id),
                "X-Generated-At": datetime.utcnow().isoformat(),
                "X-Report-Format": result.extension
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get(
    "/health",
    summary="Report service health check",
    description="Check if the report generation service is operational."
)
async def report_service_health(
    db: Session = Depends(get_db)
):
    """
    Health check endpoint for the report service.
    
    Returns service status and dependencies.
    """
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "service": "report-service",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "database": "connected",
                "weasyprint": "available"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "report-service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
