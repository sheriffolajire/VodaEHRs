"""Audit service for Phase 5.

Manages immutable, hash-chained audit logs.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditPriority
from app.repositories import audit_log_repository


class AuditService:
    """Service for managing audit logs with hash chaining."""
    
    @staticmethod
    def persist_audit_entry(
        db: Session,
        action: str,
        user_id: uuid.UUID | None,
        patient_id: uuid.UUID | None,
        status: str,
        reason: str | None = None,
        ip_address: str | None = None,
        priority: AuditPriority = AuditPriority.NORMAL
    ) -> AuditLog:
        """Persist an audit entry with hash chaining.
        
        Args:
            db: Database session
            action: Action performed (e.g., "record.view", "consent.grant")
            user_id: User who performed the action (None for system)
            patient_id: Patient affected (None if not patient-specific)
            status: "success", "failure", or "tamper_detected"
            reason: Optional reason/details
            ip_address: Optional IP address
            priority: NORMAL or HIGH (break-glass = HIGH)
        
        Returns:
            The created AuditLog entry
        """
        # Get hash of previous entry for chain
        prev_hash = audit_log_repository.get_last_hash(db)
        
        # Create entry (without hash first)
        entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            patient_id=patient_id,
            action=action,
            status=status,
            reason=reason,
            ip_address=ip_address,
            priority=priority,
            prev_hash=prev_hash,
            entry_hash="",  # Will compute after setting all fields
            created_at=datetime.now(timezone.utc)
        )
        
        # Compute hash
        entry.entry_hash = entry.compute_hash()
        
        # Persist
        return audit_log_repository.create(db, entry)
    
    @staticmethod
    def verify_chain(db: Session) -> tuple[bool, int | None]:
        """Verify the integrity of the audit log hash chain.
        
        Args:
            db: Database session
        
        Returns:
            (is_valid, broken_at_index)
            - is_valid: True if chain is intact
            - broken_at_index: Index where chain breaks (None if valid)
        """
        return audit_log_repository.verify_chain(db)
    
    @staticmethod
    def get_chain_status(db: Session) -> dict[str, Any]:
        """Get the status of the audit log chain.
        
        Args:
            db: Database session
        
        Returns:
            Dict with chain status information
        """
        return audit_log_repository.get_chain_status(db)
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        action: str | None = None,
        priority: AuditPriority | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Query audit logs with filters.
        
        Args:
            db: Database session
            user_id: Filter by user
            patient_id: Filter by patient
            action: Filter by action
            priority: Filter by priority
            skip: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of audit log entries
        """
        if user_id:
            return audit_log_repository.list_by_user(db, user_id, skip, limit)
        elif patient_id:
            return audit_log_repository.list_by_patient(db, patient_id, skip, limit)
        elif action:
            return audit_log_repository.list_by_action(db, action, skip, limit)
        elif priority == AuditPriority.HIGH:
            return audit_log_repository.list_high_priority(db, skip, limit)
        else:
            return audit_log_repository.list_all(db, skip, limit)
    
    @staticmethod
    def log_record_view(
        db: Session,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        record_id: uuid.UUID,
        is_break_glass: bool = False,
        is_admin_override: bool = False,
        ip_address: str | None = None
    ) -> AuditLog:
        """Log a record view event.
        
        Args:
            db: Database session
            user_id: User viewing the record
            patient_id: Patient whose record was viewed
            record_id: Record that was viewed
            is_break_glass: Whether this was via break-glass
            is_admin_override: Whether this was admin override
            ip_address: Optional IP address
        
        Returns:
            The created audit log entry
        """
        priority = AuditPriority.HIGH if (is_break_glass or is_admin_override) else AuditPriority.NORMAL
        
        reason = None
        if is_break_glass:
            reason = f"Emergency access (break-glass) to record {record_id}"
        elif is_admin_override:
            reason = f"Admin override to record {record_id}"
        
        return AuditService.persist_audit_entry(
            db=db,
            action="record.view",
            user_id=user_id,
            patient_id=patient_id,
            status="success",
            reason=reason,
            ip_address=ip_address,
            priority=priority
        )
    
    @staticmethod
    def log_consent_grant(
        db: Session,
        patient_id: uuid.UUID,
        clinician_id: uuid.UUID,
        record_type: str,
        ip_address: str | None = None
    ) -> AuditLog:
        """Log a consent grant event.
        
        Args:
            db: Database session
            patient_id: Patient granting consent
            clinician_id: Clinician receiving consent
            record_type: Type of records covered
            ip_address: Optional IP address
        
        Returns:
            The created audit log entry
        """
        return AuditService.persist_audit_entry(
            db=db,
            action="consent.grant",
            user_id=patient_id,
            patient_id=patient_id,
            status="success",
            reason=f"Granted consent to {clinician_id} for {record_type}",
            ip_address=ip_address,
            priority=AuditPriority.NORMAL
        )
    
    @staticmethod
    def log_consent_revoke(
        db: Session,
        patient_id: uuid.UUID,
        clinician_id: uuid.UUID,
        record_type: str,
        ip_address: str | None = None
    ) -> AuditLog:
        """Log a consent revoke event."""
        return AuditService.persist_audit_entry(
            db=db,
            action="consent.revoke",
            user_id=patient_id,
            patient_id=patient_id,
            status="success",
            reason=f"Revoked consent from {clinician_id} for {record_type}",
            ip_address=ip_address,
            priority=AuditPriority.NORMAL
        )
    
    @staticmethod
    def log_emergency_access(
        db: Session,
        clinician_id: uuid.UUID,
        patient_id: uuid.UUID,
        reason: str,
        ip_address: str | None = None
    ) -> AuditLog:
        """Log an emergency access (break-glass) request."""
        return AuditService.persist_audit_entry(
            db=db,
            action="emergency.access",
            user_id=clinician_id,
            patient_id=patient_id,
            status="success",
            reason=reason,
            ip_address=ip_address,
            priority=AuditPriority.HIGH
        )
    
    @staticmethod
    def log_tamper_detected(
        db: Session,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        record_id: uuid.UUID,
        details: str,
        ip_address: str | None = None
    ) -> AuditLog:
        """Log a tamper detection event."""
        return AuditService.persist_audit_entry(
            db=db,
            action="record.tamper_detected",
            user_id=user_id,
            patient_id=patient_id,
            status="tamper_detected",
            reason=f"Tamper detected on record {record_id}: {details}",
            ip_address=ip_address,
            priority=AuditPriority.HIGH
        )
