"""Service layer for record encryption and signature operations.

This service provides the business logic for:
- Envelope encryption of medical record content
- Digital signing of records by clinicians
- Verification of record integrity and authenticity
"""
import base64
import hashlib
import uuid
from typing import TYPE_CHECKING

from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from sqlalchemy.orm import Session

from app.crypto import encryption, keys, signatures
from app.crypto.keys import get_institutional_private_key
from app.models.signature import Signature
from app.repositories.signatures_repository import add as add_signature
from app.repositories.user_keys_repository import get_by_user_id
from app.services.exceptions import CryptoError

if TYPE_CHECKING:
    from app.models.medical_record import MedicalRecord, RecordType


class RecordCryptoService:
    """Service for encrypting, decrypting, and signing medical records."""

    @staticmethod
    def encrypt_record_content(content: str) -> tuple[bytes, bytes, bytes, bytes, bytes]:
        """Encrypt medical record content with envelope encryption.

        Creates a random AES key, encrypts the content with it, then wraps
        the AES key with the institutional public key.

        Args:
            content: The plaintext record content to encrypt.

        Returns:
            Tuple of (encrypted_data, nonce, auth_tag, wrapped_aes_key, aes_key_hash).
            - encrypted_data: The encrypted content bytes
            - nonce: The 12-byte encryption nonce
            - auth_tag: The 16-byte authentication tag
            - wrapped_aes_key: The AES key encrypted with institutional public key
            - aes_key_hash: SHA-256 hash of the plaintext content

        Raises:
            CryptoError: If encryption or key wrapping fails.
        """
        # Generate random AES key and encrypt data
        aes_key = keys.generate_aes_key()
        encrypted_data, nonce, auth_tag = encryption.encrypt_data(
            content.encode('utf-8'),
            aes_key
        )

        # Wrap AES key with institutional public key for envelope encryption
        wrapped_aes_key = keys.wrap_aes_key_with_institutional_public(aes_key)

        # Compute hash of plaintext for integrity verification
        aes_key_hash = base64.b64encode(hashlib.sha256(content.encode('utf-8')).digest()).decode('ascii')

        return encrypted_data, nonce, auth_tag, wrapped_aes_key, aes_key_hash

    @staticmethod
    def decrypt_record_content(
        encrypted_data: bytes | str,
        nonce: bytes | str,
        auth_tag: bytes | str,
        wrapped_aes_key: bytes | str,
        institution_private_key: PrivateKeyTypes | None = None
    ) -> str:
        """Decrypt medical record content.

        Unwraps the AES key with the institutional private key, then decrypts
        the record content with the unwrapped AES key.

        Args:
            encrypted_data: The encrypted content bytes (or hex string).
            nonce: The 12-byte encryption nonce (or hex string).
            auth_tag: The 16-byte authentication tag (or hex string).
            wrapped_aes_key: The AES key encrypted with institutional public key (or hex string).
            institution_private_key: Optional cached private key for performance.

        Returns:
            The decrypted plaintext record content.

        Raises:
            CryptoError: If decryption or key unwrapping fails.
        """
        # Convert string inputs to bytes if necessary
        # Database may return hex-encoded strings like "\\x1fa33b..."
        if isinstance(encrypted_data, str):
            if encrypted_data.startswith('\\x'):
                encrypted_data = bytes.fromhex(encrypted_data[2:])
            else:
                encrypted_data = encrypted_data.encode('utf-8')
        if isinstance(nonce, str):
            if nonce.startswith('\\x'):
                nonce = bytes.fromhex(nonce[2:])
            else:
                nonce = nonce.encode('utf-8')
        if isinstance(auth_tag, str):
            if auth_tag.startswith('\\x'):
                auth_tag = bytes.fromhex(auth_tag[2:])
            else:
                auth_tag = auth_tag.encode('utf-8')
        if isinstance(wrapped_aes_key, str):
            if wrapped_aes_key.startswith('\\x'):
                wrapped_aes_key = bytes.fromhex(wrapped_aes_key[2:])
            else:
                wrapped_aes_key = wrapped_aes_key.encode('utf-8')

        # Unwrap AES key with institutional private key
        if institution_private_key is None:
            institution_private_key = get_institutional_private_key()

        aes_key = keys.unwrap_aes_key_with_institutional_private(wrapped_aes_key)

        # Decrypt content with AES key
        plaintext = encryption.decrypt_data(
            encrypted_data,
            nonce,
            auth_tag,
            aes_key
        )

        return plaintext.decode('utf-8')

    @staticmethod
    def sign_record(
        db: Session,
        record_content: str,
        user_id: uuid.UUID,
        signer_private_key: PrivateKeyTypes | None = None
    ) -> Signature:
        """Sign a medical record with a clinician's private key.

        Creates a signature for the record's hash using the signer's private key.
        The private key is loaded from the database (encrypted with master key)
        if not provided.

        Args:
            db: Database session.
            record_content: The record content to sign (plaintext).
            user_id: The signer's user ID.
            signer_private_key: Optional cached private key for performance.

        Returns:
            The created Signature object.

        Raises:
            CryptoError: If key loading, signing, or database operations fail.
        """
        # Get user's key pair from database
        user_key = get_by_user_id(db, user_id)
        if user_key is None:
            raise CryptoError(f"User {user_id} has no key pair configured")

        # Decrypt user's private key from database
        if signer_private_key is None:
            from app.crypto.keys import _get_master_key, decrypt_private_key_from_storage
            master_key = _get_master_key()
            decrypted_pem = decrypt_private_key_from_storage(
                user_key.encrypted_private_key,
                master_key
            )

            from cryptography.hazmat.primitives import serialization
            signer_private_key = serialization.load_pem_private_key(
                decrypted_pem,
                password=None
            )

        # Create signature
        signature_dict = signatures.sign_record(record_content, signer_private_key)

        # Create and store Signature model
        db_signature = Signature(
            record_id=uuid.uuid4(),  # Temporary placeholder; caller replaces after flush.
            signer_id=user_id,
            signature=signature_dict["signature"],
            algorithm=signature_dict["algorithm"],
        )

        db.add(db_signature)
        db.flush()

        return db_signature

    @staticmethod
    def verify_record_signature(
        record_content: str,
        signature_b64: str,
        public_key_pem: str,
        algorithm: str
    ) -> bool:
        """Verify a record's digital signature.

        Args:
            record_content: The record content (plaintext).
            signature_b64: The base64-encoded signature.
            public_key_pem: The public key in PEM format.
            algorithm: The signature algorithm (e.g., "RSA-PSS-SHA256").

        Returns:
            True if signature is valid, False otherwise.
        """
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization

            public_key = serialization.load_pem_public_key(
                base64.b64decode(public_key_pem),
                backend=default_backend()
            )

            return signatures.verify_record_with_base64_sig(
                record_content,
                signature_b64,
                public_key,
                algorithm
            )
        except Exception:
            return False

    @staticmethod
    def create_key_pair_for_user(user_id: uuid.UUID) -> tuple[str, str]:
        """Generate a new key pair for a user and encrypt private key.

        Args:
            user_id: The user's UUID.

        Returns:
            Tuple of (public_key_pem_b64, encrypted_private_key_b64).
        """
        public_pem, encrypted_private = keys.generate_clinician_key_pair()
        return public_pem, encrypted_private

    @staticmethod
    def encrypt_and_sign_record(
        db: Session,
        patient_id: uuid.UUID,
        content: str,
        title: str,
        record_type: 'RecordType',
        summary: str,
        created_by: uuid.UUID
    ) -> 'MedicalRecord':
        """Encrypt a medical record and sign it with the creator's key.

        Combines encryption and digital signing in one operation suitable for seeding.

        Args:
            db: Database session.
            patient_id: The patient this record belongs to.
            content: The plaintext record content.
            title: The record title.
            record_type: The type of record.
            summary: A brief summary of the record.
            created_by: The user creating the record (must have key pair).

        Returns:
            The created MedicalRecord object with encrypted content and signature.

        Raises:
            CryptoError: If encryption, signing, or database operations fail.
        """
        from app.models.medical_record import MedicalRecord
        
        # Encrypt the record content
        encrypted_data, nonce, auth_tag, wrapped_aes_key, content_hash = (
            RecordCryptoService.encrypt_record_content(content)
        )
        
        # Create the basic medical record (without signature yet)
        # Store binary encrypted fields directly as ``bytes`` to match the
        # ``LargeBinary`` columns defined in ``MedicalRecord``. Previously the
        # values were base64‑encoded strings, which caused a ``bytes or buffer
        # expected`` error during SQLAlchemy flush. Using raw bytes preserves the
        # exact ciphertext and avoids unnecessary encoding/decoding overhead.
        record = MedicalRecord(
            patient_id=patient_id,
            record_type=record_type,

            # Phase 4 compatibility. This will be removed in Phase 5.
            content=content,

            title=title,
            summary=summary,

            encrypted_data=encrypted_data,
            encrypted_aes_key=wrapped_aes_key,
            nonce=nonce,
            auth_tag=auth_tag,
            hash=content_hash,

            created_by=created_by,
            version=1,
        )
        
        # Add to database and commit to get a valid record ID
        db.add(record)

        # Flush to obtain the generated primary key without committing.
        db.flush()  # Refresh to get the record with its ID
        
        try:
            # Now sign the record using the actual record ID
            signature = RecordCryptoService.sign_record(
                db=db,
                record_content=content,
                user_id=created_by,
            )

            signature.record_id = record.id

            db.add(signature)

            # Flush so both objects are written in the same transaction.
            db.flush()

            return record
        except Exception as exc:
            db.rollback()
            raise CryptoError(f"Failed to sign record: {exc}") from exc
