"""Audit log repository for Phase 5.

Provides data access for immutable, hash-chained audit logs.
"""
import uuid
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog, AuditPriority


def get_by_id(db: Session, log_id: uuid.UUID) -> AuditLog | None:
    """Get an audit log entry by ID."""
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()


def get_last_entry(db: Session) -> AuditLog | None:
    """Get the most recent audit log entry (for hash chaining)."""
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).first()


def get_last_hash(db: Session) -> str | None:
    """Get the hash of the last audit log entry (for hash chaining)."""
    last = get_last_entry(db)
    return last.entry_hash if last else None


def list_all(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """List audit log entries with pagination."""
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def list_by_user(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """List audit log entries for a specific user."""
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def list_by_patient(
    db: Session,
    patient_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """List audit log entries for a specific patient."""
    return db.query(AuditLog).filter(
        AuditLog.patient_id == patient_id
    ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def get_recent_entries(
    db: Session,
    limit: int = 10
) -> list[AuditLog]:
    """Get the most recent audit log entries."""
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()


def list_by_action(
    db: Session,
    action: str,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """List audit log entries for a specific action."""
    return db.query(AuditLog).filter(
        AuditLog.action == action
    ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def list_high_priority(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """List high-priority audit log entries (break-glass, tamper detection)."""
    return db.query(AuditLog).filter(
        AuditLog.priority == AuditPriority.HIGH
    ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def create(db: Session, entry: AuditLog) -> AuditLog:
    """Create a new audit log entry.
    
    Note: The entry_hash should already be computed before calling this.
    """
    db.add(entry)
    db.flush()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> tuple[bool, int | None]:
    """Verify the integrity of the audit log hash chain.
    
    Returns:
        (is_valid, broken_at_index)
        - is_valid: True if chain is intact
        - broken_at_index: Index where chain breaks (None if valid)
    """
    entries = db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()
    
    if not entries:
        return True, None
    
    for i, entry in enumerate(entries):
        # Verify entry hash
        if not entry.verify_hash():
            return False, i
        
        # Verify chain link (except for first entry)
        if i > 0:
            prev_entry = entries[i - 1]
            if entry.prev_hash != prev_entry.entry_hash:
                return False, i
    
    return True, None


def get_chain_status(db: Session) -> dict:
    """Get the status of the audit log chain with detailed diagnostics."""
    is_valid, broken_at = verify_chain(db)
    
    last_entry = get_last_entry(db)
    entry_count = db.query(AuditLog).count()
    
    # Build detailed diagnostics
    diagnostics = {
        "chain_ok": is_valid,
        "broken_at_index": broken_at,
        "total_entries": entry_count,
        "last_entry_time": last_entry.created_at.isoformat() if last_entry else None,
        "last_entry_hash": last_entry.entry_hash if last_entry else None,
    }
    
    if broken_at is not None:
        # Get the broken entry and previous entry for context
        entries = db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()
        if broken_at < len(entries):
            broken_entry = entries[broken_at]
            diagnostics["broken_entry"] = {
                "id": str(broken_entry.id),
                "action": broken_entry.action,
                "created_at": broken_entry.created_at.isoformat(),
                "entry_hash": broken_entry.entry_hash,
                "prev_hash": broken_entry.prev_hash,
            }
            
            if broken_at > 0:
                prev_entry = entries[broken_at - 1]
                diagnostics["previous_entry"] = {
                    "id": str(prev_entry.id),
                    "action": prev_entry.action,
                    "created_at": prev_entry.created_at.isoformat(),
                    "entry_hash": prev_entry.entry_hash,
                }
                diagnostics["expected_prev_hash"] = prev_entry.entry_hash
                diagnostics["actual_prev_hash"] = broken_entry.prev_hash
    
    return diagnostics


def repair_chain(db: Session, admin_user_id: str) -> dict:
    """Repair the audit log chain by recalculating hashes.
    
    This should only be called by an admin when the chain is broken.
    It recalculates all hashes from the beginning, creating a new valid chain.
    
    Args:
        db: Database session
        admin_user_id: ID of admin performing the repair (for logging)
        
    Returns:
        Dict with repair results
    """
    from app.models.audit_log import AuditLog
    
    entries = db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()
    
    if not entries:
        return {"repaired": False, "reason": "No entries to repair"}
    
    repaired_count = 0
    prev_hash = None
    
    for i, entry in enumerate(entries):
        # Store old hash for comparison
        old_hash = entry.entry_hash
        old_prev_hash = entry.prev_hash
        
        # Update prev_hash link
        entry.prev_hash = prev_hash
        
        # Recalculate hash
        entry.entry_hash = entry.compute_hash()
        
        # Check if this entry was modified
        if old_hash != entry.entry_hash or old_prev_hash != entry.prev_hash:
            repaired_count += 1
        
        prev_hash = entry.entry_hash
    
    db.flush()
    
    return {
        "repaired": True,
        "total_entries": len(entries),
        "repaired_entries": repaired_count,
        "message": f"Chain repaired. {repaired_count} entries updated."
    }


def get_events_by_category(
    db: Session,
    category: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """Get audit events filtered by category."""
    from app.models.audit_log import AuditCategory
    
    query = db.query(AuditLog).filter(AuditLog.category == AuditCategory(category))
    
    if from_date:
        query = query.filter(AuditLog.created_at >= from_date)
    if to_date:
        query = query.filter(AuditLog.created_at <= to_date)
    
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def get_events_by_priority(
    db: Session,
    priority: str,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    skip: int = 0,
    limit: int = 100
) -> list[AuditLog]:
    """Get audit events filtered by priority."""
    from app.models.audit_log import AuditPriority
    
    query = db.query(AuditLog).filter(AuditLog.priority == AuditPriority(priority))
    
    if from_date:
        query = query.filter(AuditLog.created_at >= from_date)
    if to_date:
        query = query.filter(AuditLog.created_at <= to_date)
    
    return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()


def get_unique_actions(db: Session) -> list[str]:
    """Get all unique action types in the audit log."""
    results = db.query(AuditLog.action).distinct().all()
    return [r[0] for r in results if r[0]]
