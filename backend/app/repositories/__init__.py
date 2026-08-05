"""Repositories package for database access.

This package provides data access layer for all models.
"""

from app.repositories import (
    appointment_repository,
    assignment_repository,
    audit_log_repository,
    consent_repository,
    document_repository,
    emergency_access_repository,
    patient_repository,
    record_repository,
    record_version_repository,
    role_repository,
    signatures_repository,
    user_keys_repository,
    user_repository,
)

__all__ = [
    "appointment_repository",
    "assignment_repository",
    "audit_log_repository",
    "consent_repository",
    "document_repository",
    "emergency_access_repository",
    "patient_repository",
    "record_repository",
    "record_version_repository",
    "role_repository",
    "signatures_repository",
    "user_keys_repository",
    "user_repository",
]
