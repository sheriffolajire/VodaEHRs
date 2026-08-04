"""Medical record business logic (access-controlled + audited)."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
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

    # Log creation audit event
    record_event(
        AuditEvent(
            action="record.create",
            user_id=str(actor.id),
            patient_id=str(payload.patient_id),
            status="success",
            reason=str(record.id),
        )
    )

    # Return the newly created record
    return record


def list_records(db: Session, actor: User, patient_id: uuid.UUID) -> list[MedicalRecord]:
    """Return a list of records for a patient that the actor is authorized to access.

    The function first checks that ``actor`` has permission to view the patient
    using :func:`app.services.authorization.ensure_patient_access`. If the check
    passes, it delegates to :func:`app.repositories.record_repository.list_for_patient`
    to retrieve the records ordered by creation time (newest first).
    """
    # Verify access to the patient; will raise NotFoundError or PermissionError_ if not allowed.
    authorization.ensure_patient_access(db, actor, patient_id)
    return record_repository.list_for_patient(db, patient_id)


def get_record(db: Session, actor: User, record_id: uuid.UUID) -> MedicalRecord:
    """Fetch a single record by its ID after confirming the actor can access the patient.

    Raises ``NotFoundError`` if the record does not exist and ``PermissionError_``
    if the actor is not authorized to view the associated patient.
    """
    record = record_repository.get_by_id(db, record_id)
    if record is None:
        raise NotFoundError("Record not found.")
    # Ensure the actor has access to the patient linked to this record.
    authorization.ensure_patient_access(db, actor, record.patient_id)
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