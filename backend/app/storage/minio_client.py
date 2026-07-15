"""MinIO (S3-compatible) object storage client configuration.

Provides a lazily-created Boto3 S3 client. Upload/download flows are
implemented in Phase 3.
"""

from functools import lru_cache

import boto3
from botocore.client import Config

from app.core.config import settings


@lru_cache
def get_storage_client():
    """Return a cached Boto3 S3 client configured for MinIO."""
    scheme = "https" if settings.minio_secure else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )
