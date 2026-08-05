"""Record version history API endpoints for Phase 5.

View immutable version history of records.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.user import User
from app.schemas.response import success
from app.services import version_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/records", tags=["record-versions"])


@router.get("/{record_id}/versions")
def list_record_versions(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """List version history for a record.
    
    Returns all versions of the record in chronological order.
    """
    try:
        # TODO: Add authorization check - must have access to the record
        versions = version_service.VersionService.list_versions(db, record_id)
        
        result = []
        for v in versions:
            result.append({
                "id": str(v.id),
                "record_id": str(v.record_id),
                "version": v.version,
                "hash": v.hash,
                "created_by": str(v.created_by),
                "created_at": v.created_at.isoformat()
            })
        
        return success(data=result)
    except NotFoundError as exc:
        raise to_http_error(exc) from exc


@router.get("/{record_id}/versions/{version}")
def get_record_version(
    record_id: uuid.UUID,
    version: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get a specific version of a record.
    
    Returns the version details including encrypted data snapshot.
    """
    try:
        # TODO: Add authorization check - must have access to the record
        v = version_service.VersionService.get_version(db, record_id, version)
        
        if not v:
            raise NotFoundError(f"Version {version} not found for record {record_id}")
        
        return success(
            data={
                "id": str(v.id),
                "record_id": str(v.record_id),
                "version": v.version,
                "hash": v.hash,
                "created_by": str(v.created_by),
                "created_at": v.created_at.isoformat(),
                "encrypted_data_size": len(v.encrypted_data),
                "encrypted_aes_key_size": len(v.encrypted_aes_key),
                "nonce_size": len(v.nonce),
                "auth_tag_size": len(v.auth_tag)
            }
        )
    except NotFoundError as exc:
        raise to_http_error(exc) from exc


@router.get("/{record_id}/versions/latest")
def get_latest_version(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get the latest version of a record."""
    try:
        # TODO: Add authorization check - must have access to the record
        v = version_service.VersionService.get_latest_version(db, record_id)
        
        if not v:
            raise NotFoundError(f"No versions found for record {record_id}")
        
        return success(
            data={
                "id": str(v.id),
                "record_id": str(v.record_id),
                "version": v.version,
                "hash": v.hash,
                "created_by": str(v.created_by),
                "created_at": v.created_at.isoformat()
            }
        )
    except NotFoundError as exc:
        raise to_http_error(exc) from exc


@router.get("/{record_id}/versions/count")
def get_version_count(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get the number of versions for a record."""
    try:
        count = version_service.VersionService.get_version_count(db, record_id)
        return success(data={"count": count})
    except Exception as exc:
        raise to_http_error(exc) from exc
