"""Object-storage operations for medical documents (MinIO / S3).

The database stores metadata; this module moves the actual bytes to and from
object storage. Storage keys are always server-generated.
"""

import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import BinaryIO
import secrets

from botocore.exceptions import ClientError

from app.core.config import settings
from app.models.medical_document import UploadPurpose
from app.storage.minio_client import get_storage_client


def ensure_bucket() -> None:
    """Create the documents bucket if it does not already exist.

    Called once on application startup so uploads never fail on a missing bucket.
    """
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)


def _normalize_extension(filename: str) -> str:
    """Extract and normalize file extension for security.
    
    Returns lowercase extension without the dot, or 'bin' for unknown types.
    """
    ext = Path(filename).suffix.lower().lstrip('.')
    # Security: only allow alphanumeric extensions
    if not ext or not ext.isalnum() or len(ext) > 10:
        return 'bin'
    return ext


def _sanitize_purpose(purpose: UploadPurpose) -> str:
    """Convert purpose enum to safe directory name."""
    return purpose.value.replace('_', '-')


def _sanitize_readable_name(name: str) -> str:
    """Convert a name to a safe, readable string for filenames.
    
    Removes/replaces special characters, spaces become hyphens.
    """
    # Replace common separators with hyphen
    sanitized = name.replace(" ", "-").replace("_", "-").replace(".", "-")
    # Remove any non-alphanumeric characters except hyphens
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "-")
    # Collapse multiple hyphens
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    # Strip leading/trailing hyphens and lowercase
    sanitized = sanitized.strip("-").lower()
    return sanitized[:50]  # Limit length


def build_storage_key(
    patient_id: uuid.UUID,
    patient_name: str,
    filename: str,
    purpose: UploadPurpose = UploadPurpose.GENERAL,
    document_id: uuid.UUID | None = None
) -> str:
    """Build a secure, organized, collision-free object key with readable names.
    
    Format: {patient_id}/{purpose}/{yyyy}/{mm}/{dd}/{patient-name}_{purpose}_{date}_{short-id}.{ext}
    
    Args:
        patient_id: UUID of the patient (natural partitioning)
        patient_name: Patient's full name for readable filename
        filename: Original filename (only extension is used)
        purpose: Upload purpose/category for organization
        document_id: Document record UUID for traceability
        
    Returns:
        Server-generated storage key with readable filename (no original filename exposed)
    """
    # Use document_id if provided, otherwise generate new UUID
    doc_uuid = document_id or uuid.uuid4()
    short_id = doc_uuid.hex[:8]  # First 8 chars of UUID for brevity
    
    # Get normalized extension
    ext = _normalize_extension(filename)
    
    # Build date-based path for organization
    now = datetime.now(UTC)
    date_path = f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
    date_str = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"
    
    # Build purpose directory and readable purpose string
    purpose_dir = _sanitize_purpose(purpose)
    purpose_readable = purpose_dir
    
    # Build readable patient name
    patient_readable = _sanitize_readable_name(patient_name) if patient_name else str(patient_id)[:8]
    
    # Construct readable filename: patient-purpose-date-shortid.ext
    readable_filename = f"{patient_readable}_{purpose_readable}_{date_str}_{short_id}.{ext}"
    
    # Construct final key: patient/purpose/date/readable_filename
    storage_key = f"{patient_id}/{purpose_dir}/{date_path}/{readable_filename}"
    
    return storage_key


def build_storage_key_legacy(patient_id: uuid.UUID, filename: str) -> str:
    """Legacy key builder for backward compatibility.
    
    Kept for migration purposes. New uploads should use build_storage_key().
    """
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"{patient_id}/{uuid.uuid4()}/{safe_name}"


def put_object(storage_key: str, data: BinaryIO, content_type: str) -> None:
    """Upload a file object to storage under the given key."""
    client = get_storage_client()
    client.upload_fileobj(
        data,
        settings.minio_bucket,
        storage_key,
        ExtraArgs={"ContentType": content_type},
    )


def open_object_stream(storage_key: str):
    """Return a streaming body for the stored object (caller iterates/closes)."""
    client = get_storage_client()
    response = client.get_object(Bucket=settings.minio_bucket, Key=storage_key)
    return response["Body"]


def get_bucket_size() -> int:
    """Get the total size of all objects in the documents bucket in bytes.
    
    Returns:
        Total size in bytes, or 0 if bucket doesn't exist or error occurs.
    """
    client = get_storage_client()
    total_size = 0
    try:
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=settings.minio_bucket):
            for obj in page.get("Contents", []):
                total_size += obj.get("Size", 0)
    except ClientError:
        # Bucket doesn't exist or other error
        pass
    return total_size
