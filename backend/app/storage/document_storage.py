"""Object-storage operations for medical documents (MinIO / S3).

The database stores metadata; this module moves the actual bytes to and from
object storage. Storage keys are always server-generated.
"""

import uuid
from typing import BinaryIO

from botocore.exceptions import ClientError

from app.core.config import settings
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


def build_storage_key(patient_id: uuid.UUID, filename: str) -> str:
    """Build a collision-free, traversal-safe object key.

    The client filename is kept only as a trailing label; a random UUID segment
    guarantees uniqueness and prevents one upload overwriting another.
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
