"""Record version service for Phase 5.

Manages immutable record version history.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.record_version import RecordVersion
from app.repositories import record_version_repository


class VersionService:
    """Service for managing record version history."""
    
    @staticmethod
    def create_version(
        db: Session,
        record_id: uuid.UUID,
        encrypted_data: bytes,
        encrypted_aes_key: bytes,
        nonce: bytes,
        auth_tag: bytes,
        hash_value: str,
        created_by: uuid.UUID
    ) -> RecordVersion:
        """Create a new version snapshot for a record.
        
        This is called when a record is updated. The current state is
        snapshotted before the update is applied.
        
        Args:
            db: Database session
            record_id: The record being versioned
            encrypted_data: Encrypted content snapshot
            encrypted_aes_key: Wrapped AES key snapshot
            nonce: AES-GCM nonce
            auth_tag: AES-GCM auth tag
            hash_value: SHA-256 hash of plaintext
            created_by: User creating this version
        
        Returns:
            The created RecordVersion
        """
        # Get next version number
        version_num = record_version_repository.get_next_version_number(db, record_id)
        
        version = RecordVersion(
            record_id=record_id,
            version=version_num,
            encrypted_data=encrypted_data,
            encrypted_aes_key=encrypted_aes_key,
            nonce=nonce,
            auth_tag=auth_tag,
            hash=hash_value,
            created_by=created_by
        )
        
        return record_version_repository.create(db, version)
    
    @staticmethod
    def list_versions(
        db: Session,
        record_id: uuid.UUID
    ) -> list[RecordVersion]:
        """List all versions for a record.
        
        Args:
            db: Database session
            record_id: The record
        
        Returns:
            List of versions ordered by version number
        """
        return record_version_repository.list_for_record(db, record_id)
    
    @staticmethod
    def get_version(
        db: Session,
        record_id: uuid.UUID,
        version: int
    ) -> RecordVersion | None:
        """Get a specific version of a record.
        
        Args:
            db: Database session
            record_id: The record
            version: Version number
        
        Returns:
            The RecordVersion or None if not found
        """
        return record_version_repository.get_by_record_and_version(
            db, record_id, version
        )
    
    @staticmethod
    def get_latest_version(
        db: Session,
        record_id: uuid.UUID
    ) -> RecordVersion | None:
        """Get the latest version for a record.
        
        Args:
            db: Database session
            record_id: The record
        
        Returns:
            The latest RecordVersion or None if no versions
        """
        return record_version_repository.get_latest_version(db, record_id)
    
    @staticmethod
    def get_version_count(
        db: Session,
        record_id: uuid.UUID
    ) -> int:
        """Get the number of versions for a record.
        
        Args:
            db: Database session
            record_id: The record
        
        Returns:
            Number of versions
        """
        versions = record_version_repository.list_for_record(db, record_id)
        return len(versions)
