"""Medical record business logic (access-controlled + audited)."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.audit_log import AuditPriority
from app.models.medical_record import MedicalRecord, RecordType
from app.models.role import RoleName
from app.models.user import User
from app.repositories import record_repository
from app.schemas.record import RecordCreate, RecordSignature
from app.services import authorization
from app.services.exceptions import NotFoundError, PermissionError_, CryptoError
from app.services.record_crypto_service import RecordCryptoService
from app.services.user_keys_service import UserKeysService
import base64
from cryptography.hazmat.primitives import serialization
from app.crypto import signatures
from cryptography.hazmat.backends import default_backend
import time

# Simple in‑memory rate limiter for decryption (max 5 calls per minute per record)
_decryption_calls_record: dict[uuid.UUID, list[float]] = {}

def _check_decryption_rate_record(record_id: uuid.UUID, limit: int = 5, period: int = 60) -> None:
    """Raise ``CryptoError`` if a record is decrypted more than ``limit`` times in ``period`` seconds.

    This mitigates abuse of the decryption endpoint (e.g., brute‑forcing content).
    """
    now = time.time()
    timestamps = _decryption_calls_record.get(record_id, [])
    # Keep only timestamps within the period
    timestamps = [t for t in timestamps if now - t < period]
    if len(timestamps) >= limit:
        raise CryptoError("Decryption rate limit exceeded for this record. Please try again later.")
    timestamps.append(now)
    _decryption_calls_record[record_id] = timestamps


def create_record(db: Session, actor: User, payload: RecordCreate) -> MedicalRecord:
    """Create a record for an assigned patient.

    Nurses may only write nursing notes; other record types require a doctor.
    """
    authorization.ensure_patient_access(db, actor, payload.patient_id)

    if actor.role.name == RoleName.NURSE and payload.record_type != RecordType.NURSING_NOTE:
        raise PermissionError_("Nurses may only create nursing notes.")

    # Phase 4: Encrypt record content with envelope encryption
    # Ensure required non‑null fields have safe defaults. The database schema
    # defines ``title`` and ``summary`` as NOT NULL, but the frontend may omit
    # them. Providing defaults prevents IntegrityError while preserving the
    # ability to edit them later.
    title = payload.title if payload.title is not None else "Untitled Record"
    summary = payload.summary if payload.summary is not None else ""

    encrypted_data, nonce, auth_tag, wrapped_aes_key, hash_value = RecordCryptoService.encrypt_record_content(
        payload.content
    )

    record = record_repository.add(
        db,
        MedicalRecord(
            patient_id=payload.patient_id,
            record_type=payload.record_type,
            title=title,
            summary=summary,
            encrypted_data=encrypted_data,
            nonce=nonce,
            auth_tag=auth_tag,
            encrypted_aes_key=wrapped_aes_key,
            hash=hash_value,
            created_by=actor.id,
        ),
    )

    # Phase 4: Sign the record with clinician's private key
    # Sign the record with the clinician's private key
    UserKeysService.sign_record(db, record.id, actor.id, payload.content)

    # Log creation audit event (legacy file logging)
    record_event(
        AuditEvent(
            action="record.create",
            user_id=str(actor.id),
            patient_id=str(payload.patient_id),
            status="success",
            reason=str(record.id),
        )
    )
    
    # Persist to database audit log (Phase 5)
    from app.services.audit_service import AuditService
    AuditService.persist_audit_entry(
        db=db,
        action="record.create",
        user_id=actor.id,
        patient_id=payload.patient_id,
        status="success",
        reason=f"Created {payload.record_type.value} record: {record.title}",
        ip_address=None,
        priority=AuditPriority.NORMAL
    )

    # Return the newly created record
    return record


def list_records_all(
    db: Session, 
    actor: User, 
    patient_id: uuid.UUID,
    is_admin_override: bool = False
) -> list[MedicalRecord]:
    """Return ALL records for a patient (for listing with metadata).
    
    This returns all records to clinicians with patient access, but the API layer
    will filter content based on consent. This allows clinicians to see that
    records exist (count, type, date) but not view content without consent.
    
    Phase 5: 
    1. Identity (JWT token)
    2. Role (require_role) - checked at API layer
    3. Resource Access (ensure_patient_access)
    4. Content filtering done at API layer based on consent
    
    Audit entries are created for each record viewed.
    """
    # Layer 3: Verify access to the patient
    authorization.ensure_patient_access(db, actor, patient_id)
    
    # Get all records for the patient
    all_records = record_repository.list_for_patient(db, patient_id)
    
    # Audit each record view
    from app.services.audit_service import AuditService
    for record in all_records:
        AuditService.log_record_view(
            db,
            user_id=actor.id,
            patient_id=patient_id,
            record_id=record.id,
            is_break_glass=False,
            is_admin_override=is_admin_override
        )
    
    return all_records


def list_records(
    db: Session, 
    actor: User, 
    patient_id: uuid.UUID,
    is_admin_override: bool = False
) -> list[MedicalRecord]:
    """Return a list of records for a patient that the actor is authorized to access.

    Phase 5: Adds Layer 4 consent check for each record. Access requires:
    1. Identity (JWT token)
    2. Role (require_role) - checked at API layer
    3. Resource Access (ensure_patient_access)
    4. Consent (ensure_consent) - checked for EACH record (patients exempt)
    5. Integrity (decrypt + verify) - done at API layer

    The function filters out records that the actor doesn't have consent to view.
    Patients can always view their own records (consent not required).
    Audit entries are created for each record viewed.
    """
    # Layer 3: Verify access to the patient
    authorization.ensure_patient_access(db, actor, patient_id)
    
    # Get all records for the patient
    all_records = record_repository.list_for_patient(db, patient_id)
    
    # Patients can see all their own records - no consent check needed
    if actor.role.name == RoleName.PATIENT:
        # Audit each record view
        from app.services.audit_service import AuditService
        for record in all_records:
            AuditService.log_record_view(
                db,
                user_id=actor.id,
                patient_id=patient_id,
                record_id=record.id,
                is_break_glass=False,
                is_admin_override=is_admin_override
            )
        return all_records
    
    # Layer 4: For clinicians, filter records based on consent
    # BUT: Record creators can always view their own records
    visible_records = []
    for record in all_records:
        # Record creator can always view their own records
        if record.created_by == actor.id:
            visible_records.append(record)
            
            # Audit each record view
            from app.services.audit_service import AuditService
            AuditService.log_record_view(
                db,
                user_id=actor.id,
                patient_id=patient_id,
                record_id=record.id,
                is_break_glass=False,
                is_admin_override=is_admin_override
            )
            continue
        
        # For non-creators, check consent
        try:
            authorization.ensure_consent(
                db, actor, patient_id, record.record_type, is_admin_override
            )
            visible_records.append(record)
            
            # Audit each record view
            from app.services.audit_service import AuditService
            AuditService.log_record_view(
                db,
                user_id=actor.id,
                patient_id=patient_id,
                record_id=record.id,
                is_break_glass=False,
                is_admin_override=is_admin_override
            )
        except PermissionError_:
            # No consent for this record type - skip it (don't reveal existence)
            continue
    
    return visible_records


def get_record(
    db: Session,
    actor: User,
    record_id: uuid.UUID,
    is_admin_override: bool = False
) -> MedicalRecord:
    """Fetch a single record by its ID after confirming the actor can access the patient.

    Phase 5: Adds Layer 4 consent check. Access requires:
    1. Identity (JWT token)
    2. Role (require_role)
    3. Resource Access (ensure_patient_access)
    4. Consent (ensure_consent) ← THIS CHECK
    5. Integrity (decrypt + verify)

    Break-glass bypasses Layer 4 only, with mandatory reason + 30min expiry.
    Admin override is allowed but must be explicitly audited.

    Raises ``NotFoundError`` if the record does not exist and ``PermissionError_``
    if the actor is not authorized to view the associated patient or lacks consent.
    """
    record = record_repository.get_by_id(db, record_id)
    if record is None:
        raise NotFoundError("Record not found.")
    
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, record.patient_id)
    
    # Layer 4: Consent (can be bypassed by break-glass, admin override, OR if actor is the creator)
    # Record creators can always view their own records
    if record.created_by != actor.id:
        # Only check consent if the actor is NOT the creator
        authorization.ensure_consent(
            db, actor, record.patient_id, record.record_type, is_admin_override
        )
    
    # Audit the access
    from app.services.audit_service import AuditService
    AuditService.log_record_view(
        db,
        user_id=actor.id,
        patient_id=record.patient_id,
        record_id=record.id,
        is_break_glass=False,  # Will be detected by ensure_consent if used
        is_admin_override=is_admin_override
    )
    
    return record


def update_record(
    db: Session,
    actor: User,
    record_id: uuid.UUID,
    content: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    is_admin_override: bool = False
) -> MedicalRecord:
    """Update a record with new content, creating a version snapshot first.

    Phase 5: Adds Layer 4 consent check and automatic versioning.
    
    Args:
        db: Database session
        actor: User making the update
        record_id: Record to update
        content: New encrypted content (if changing)
        title: New title (if changing)
        summary: New summary (if changing)
        is_admin_override: Whether this is an admin bypass
    
    Returns:
        Updated MedicalRecord
    """
    record = record_repository.get_by_id(db, record_id)
    if record is None:
        raise NotFoundError("Record not found.")
    
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, record.patient_id)
    
    # Layer 4: Consent
    authorization.ensure_consent(
        db, actor, record.patient_id, record.record_type, is_admin_override
    )
    
    # Phase 5: Create version snapshot before updating
    from app.services.version_service import VersionService
    
    # Get current decrypted content for versioning
    current_content = get_decrypted_record_content(record)
    
    # Create version snapshot
    VersionService.create_version(
        db,
        record_id=record.id,
        encrypted_data=record.encrypted_data,
        encrypted_aes_key=record.encrypted_aes_key,
        nonce=record.nonce,
        auth_tag=record.auth_tag,
        hash_value=record.hash,
        created_by=actor.id
    )
    
    # Apply updates
    if content is not None:
        # Re-encrypt new content
        encrypted_data, nonce, auth_tag, wrapped_aes_key, hash_value = RecordCryptoService.encrypt_record_content(
            content
        )
        record.encrypted_data = encrypted_data
        record.nonce = nonce
        record.auth_tag = auth_tag
        record.encrypted_aes_key = wrapped_aes_key
        record.hash = hash_value
        
        # Re-sign with actor's key
        from app.services.user_keys_service import UserKeysService
        UserKeysService.sign_record(db, record.id, actor.id, content)
    
    if title is not None:
        record.title = title
    
    if summary is not None:
        record.summary = summary
    
    # Save updates
    record = record_repository.update(db, record)
    
    # Audit the update
    from app.services.audit_service import AuditService
    AuditService.persist_audit_entry(
        db=db,
        action="record.update",
        user_id=actor.id,
        patient_id=record.patient_id,
        status="success",
        reason=f"Updated record {record_id}",
        priority=AuditPriority.HIGH if is_admin_override else AuditPriority.NORMAL
    )
    
    return record


def get_decrypted_record_content(record: MedicalRecord) -> str:
    """Decrypt a record's content with rate‑limiting and audit logging.

    The function enforces a simple per‑record rate limit (default 5 calls per
    minute) to mitigate abuse of the decryption endpoint. It then attempts to
    unwrap the AES key using the institutional private key and decrypt the
    encrypted payload.
    """
    # Rate‑limit decryption attempts per record
    _check_decryption_rate_record(record.id)

    try:
        return RecordCryptoService.decrypt_record_content(
            record.encrypted_data,
            record.nonce,
            record.auth_tag,
            record.encrypted_aes_key,
        )
    except CryptoError as exc:
        # Audit decryption failure – user context is unknown here.
        record_event(
            AuditEvent(
                action="record.decrypt_failure",
                user_id="unknown",
                patient_id=str(record.patient_id),
                status="failure",
                reason=str(exc),
            )
        )
        raise


def verify_record_integrity(record: MedicalRecord, content: str) -> tuple[bool, list[RecordSignature]]:
    """Verify all signatures on a record and return verification status.

    For each stored ``Signature`` we fetch the signer's public key from the
    ``user_keys`` table and verify the base64‑encoded signature against the
    plaintext ``content`` using the algorithm recorded on the signature.
    The function returns ``True`` only if **all** signatures are valid.
    """
    from app.repositories.signatures_repository import get_by_record_id
    from app.services.user_keys_service import UserKeysService
    from app.crypto.signatures import verify_record_with_base64_sig
    from base64 import b64decode

    signatures = get_by_record_id(record._sa_instance_state.session, record.id)
    all_valid = True
    signature_infos: list[RecordSignature] = []

    for sig in signatures:
        # Load the signer's public key (stored encrypted, decrypt similarly to private key)
        user_key = UserKeysService.get_user_key_pair(record._sa_instance_state.session, sig.signer_id)
        # Decrypt the stored public key (it is stored plain PEM base64, no encryption)
        public_key_pem = user_key.public_key
        # Verify signature
        try:
            is_valid = verify_record_with_base64_sig(
                content,
                sig.signature,
                public_key_pem,
                sig.algorithm,
            )
        except Exception:
            is_valid = False
        if not is_valid:
            all_valid = False
        signature_infos.append(
            RecordSignature(
                signer_id=sig.signer_id,
                algorithm=sig.algorithm,
                created_at=sig.created_at,
            )
        )

    # If there are no signatures, fall back to hash presence as a weak integrity check
    if not signatures:
        all_valid = record.hash is not None

    return all_valid, signature_infos