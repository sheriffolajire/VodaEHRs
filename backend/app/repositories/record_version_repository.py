"""Record version repository for Phase 5.

Provides data access for record version history.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.record_version import RecordVersion


def get_by_id(db: Session, version_id: uuid.UUID) -> RecordVersion | None:
    """Get a record version by ID."""
    return db.query(RecordVersion).filter(RecordVersion.id == version_id).first()


def get_by_record_and_version(
    db: Session,
    record_id: uuid.UUID,
    version: int
) -> RecordVersion | None:
    """Get a specific version of a record."""
    return db.query(RecordVersion).filter(
        RecordVersion.record_id == record_id,
        RecordVersion.version == version
    ).first()


def list_for_record(db: Session, record_id: uuid.UUID) -> list[RecordVersion]:
    """List all versions for a record, ordered by version number."""
    return db.query(RecordVersion).filter(
        RecordVersion.record_id == record_id
    ).order_by(RecordVersion.version.asc()).all()


def get_latest_version(db: Session, record_id: uuid.UUID) -> RecordVersion | None:
    """Get the latest version for a record."""
    return db.query(RecordVersion).filter(
        RecordVersion.record_id == record_id
    ).order_by(RecordVersion.version.desc()).first()


def create(db: Session, version: RecordVersion) -> RecordVersion:
    """Create a new record version."""
    db.add(version)
    db.flush()
    db.refresh(version)
    return version


def get_next_version_number(db: Session, record_id: uuid.UUID) -> int:
    """Get the next version number for a record."""
    latest = get_latest_version(db, record_id)
    if latest:
        return latest.version + 1
    return 1
