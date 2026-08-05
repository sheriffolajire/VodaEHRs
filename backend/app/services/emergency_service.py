"""Emergency access (break-glass) service for Phase 5.

Manages emergency access requests that bypass consent in urgent situations.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.emergency_access import EmergencyAccess, EMERGENCY_ACCESS_DURATION_MINUTES
from app.models.user import User
from app.repositories import emergency_access_repository
from app.services.exceptions import NotFoundError, PermissionError_, ValidationError


class EmergencyService:
    """Service for managing emergency access (break-glass) requests."""
    
    @staticmethod
    def request_emergency_access(
        db: Session,
        clinician: User,
        patient_id: uuid.UUID,
        reason: str
    ) -> EmergencyAccess:
        """Request emergency access to a patient's records.
        
        Args:
            db: Database session
            clinician: The clinician requesting access (must be a doctor)
            patient_id: The patient to access
            reason: Mandatory justification (min 20 characters)
        
        Returns:
            The created EmergencyAccess object
        
        Raises:
            PermissionError_: If user is not a doctor
            ValidationError: If reason is too short
        """
        from app.models.role import RoleName
        
        if clinician.role.name != RoleName.DOCTOR:
            raise PermissionError_("Only doctors can request emergency access.")
        
        if not reason or len(reason.strip()) < 20:
            raise ValidationError(
                "Emergency access requires a detailed reason (minimum 20 characters)."
            )
        
        # Check if active emergency access already exists
        existing = emergency_access_repository.get_active_for_clinician_patient(
            db, clinician.id, patient_id
        )
        
        if existing:
            # Extend existing emergency access
            existing.expires_at = datetime.utcnow() + timedelta(
                minutes=EMERGENCY_ACCESS_DURATION_MINUTES
            )
            db.flush()
            db.refresh(existing)
            return existing
        
        # Create new emergency access request (pending approval)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        emergency = EmergencyAccess(
            clinician_id=clinician.id,
            patient_id=patient_id,
            reason=reason.strip(),
            granted_at=now,  # Set granted_at but status is pending
            expires_at=now + timedelta(minutes=EMERGENCY_ACCESS_DURATION_MINUTES),
            status="pending",  # Requires admin approval
            revoked_at=None,
            revoked_by=None,
            reviewed_by=None,
            reviewed_at=None,
            review_notes=None
        )
        
        return emergency_access_repository.create(db, emergency)
    
    @staticmethod
    def has_active_emergency_access(
        db: Session,
        clinician_id: uuid.UUID,
        patient_id: uuid.UUID
    ) -> bool:
        """Check if active emergency access exists.
        
        Args:
            db: Database session
            clinician_id: The clinician
            patient_id: The patient
        
        Returns:
            True if active emergency access exists
        """
        return emergency_access_repository.has_active_emergency_access(
            db, clinician_id, patient_id
        )
    
    @staticmethod
    def approve_emergency_access(
        db: Session,
        admin: User,
        emergency_id: uuid.UUID,
        notes: str | None = None
    ) -> EmergencyAccess:
        """Approve an emergency access request.
        
        Args:
            db: Database session
            admin: The admin approving the request
            emergency_id: ID of the emergency access to approve
            notes: Optional review notes
        
        Returns:
            The approved EmergencyAccess object
        
        Raises:
            NotFoundError: If emergency access not found
            PermissionError_: If user is not an admin
            ValidationError: If already approved/rejected
        """
        from app.models.role import RoleName
        from datetime import timezone
        
        if admin.role.name != RoleName.ADMIN:
            raise PermissionError_("Only admins can approve emergency access.")
        
        emergency = emergency_access_repository.get_by_id(db, emergency_id)
        
        if not emergency:
            raise NotFoundError("Emergency access request not found.")
        
        if emergency.status != "pending":
            raise ValidationError(f"Emergency access is already {emergency.status}.")
        
        # Update status
        emergency.status = "approved"
        emergency.reviewed_by = admin.id
        emergency.reviewed_at = datetime.now(timezone.utc)
        emergency.review_notes = notes
        
        # Update expires_at to start from approval time
        emergency.expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=EMERGENCY_ACCESS_DURATION_MINUTES
        )
        
        db.flush()
        db.refresh(emergency)
        return emergency
    
    @staticmethod
    def reject_emergency_access(
        db: Session,
        admin: User,
        emergency_id: uuid.UUID,
        notes: str | None = None
    ) -> EmergencyAccess:
        """Reject an emergency access request.
        
        Args:
            db: Database session
            admin: The admin rejecting the request
            emergency_id: ID of the emergency access to reject
            notes: Optional review notes (recommended)
        
        Returns:
            The rejected EmergencyAccess object
        
        Raises:
            NotFoundError: If emergency access not found
            PermissionError_: If user is not an admin
            ValidationError: If already approved/rejected
        """
        from app.models.role import RoleName
        from datetime import timezone
        
        if admin.role.name != RoleName.ADMIN:
            raise PermissionError_("Only admins can reject emergency access.")
        
        emergency = emergency_access_repository.get_by_id(db, emergency_id)
        
        if not emergency:
            raise NotFoundError("Emergency access request not found.")
        
        if emergency.status != "pending":
            raise ValidationError(f"Emergency access is already {emergency.status}.")
        
        # Update status
        emergency.status = "rejected"
        emergency.reviewed_by = admin.id
        emergency.reviewed_at = datetime.now(timezone.utc)
        emergency.review_notes = notes
        
        db.flush()
        db.refresh(emergency)
        return emergency
    
    @staticmethod
    def revoke_emergency_access(
        db: Session,
        admin: User,
        emergency_id: uuid.UUID
    ) -> EmergencyAccess:
        """Revoke an emergency access early.
        
        Args:
            db: Database session
            admin: The admin revoking access
            emergency_id: ID of the emergency access to revoke
        
        Returns:
            The revoked EmergencyAccess object
        
        Raises:
            NotFoundError: If emergency access not found
            PermissionError_: If user is not an admin
        """
        from app.models.role import RoleName
        
        if admin.role.name != RoleName.ADMIN:
            raise PermissionError_("Only admins can revoke emergency access.")
        
        emergency = emergency_access_repository.revoke(db, emergency_id, admin.id)
        
        if not emergency:
            raise NotFoundError("Emergency access not found or already revoked.")
        
        return emergency
    
    @staticmethod
    def list_emergency_access_for_patient(
        db: Session,
        patient_id: uuid.UUID
    ) -> list[EmergencyAccess]:
        """List all emergency access requests for a patient.
        
        Args:
            db: Database session
            patient_id: The patient
        
        Returns:
            List of emergency access requests
        """
        return emergency_access_repository.list_for_patient(db, patient_id)
    
    @staticmethod
    def list_active_emergency_access(
        db: Session
    ) -> list[EmergencyAccess]:
        """List all currently active emergency access grants.
        
        Args:
            db: Database session
        
        Returns:
            List of active emergency access grants
        """
        return emergency_access_repository.list_active(db)
    
    @staticmethod
    def get_remaining_minutes(
        db: Session,
        clinician_id: uuid.UUID,
        patient_id: uuid.UUID
    ) -> float:
        """Get remaining minutes of emergency access.
        
        Args:
            db: Database session
            clinician_id: The clinician
            patient_id: The patient
        
        Returns:
            Remaining minutes (0 if not active)
        """
        emergency = emergency_access_repository.get_active_for_clinician_patient(
            db, clinician_id, patient_id
        )
        
        if not emergency:
            return 0.0
        
        return emergency.get_remaining_minutes()
