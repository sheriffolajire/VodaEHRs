"""Audit logging interface with a minimal event schema.

Phase 1 emits audit events to the dedicated audit log stream. Persisting audit
events to the database is introduced in Phase 2.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.core.logging import get_logger

_audit_logger = get_logger("audit")


@dataclass
class AuditEvent:
    """Minimal audit event schema."""

    action: str
    user_id: str | None = None
    patient_id: str | None = None
    status: str = "success"
    reason: str | None = None
    ip_address: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def record_event(event: AuditEvent) -> None:
    """Emit an audit event to the audit log stream."""
    _audit_logger.info(
        "action=%s user_id=%s patient_id=%s status=%s reason=%s ip=%s ts=%s",
        event.action,
        event.user_id,
        event.patient_id,
        event.status,
        event.reason,
        event.ip_address,
        event.timestamp,
    )
