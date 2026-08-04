"""User key management service.

This service provides operations for managing user key pairs used in
digital signatures and encryption operations.
"""
import uuid

from sqlalchemy.orm import Session

from app.crypto import keys
from app.models.user_keys import UserKey
from app.repositories.user_keys_repository import add as add_user_key
from app.repositories.user_keys_repository import get_by_user_id
from app.services.exceptions import CryptoError, NotFoundError


class UserKeysService:
    """Service for managing user key pairs."""

    @staticmethod
    def generate_key_pair_for_user(db: Session, user_id: uuid.UUID) -> tuple[str, str]:
        """Generate a new key pair for a user.

        Args:
            db: Database session.
            user_id: The user's UUID.

        Returns:
            Tuple of (public_key_pem_b64, encrypted_private_key_b64).

        Raises:
            CryptoError: If key generation fails.
        """
        public_pem, encrypted_private = keys.generate_clinician_key_pair()

        user_key = UserKey(
            user_id=user_id,
            public_key=public_pem,
            encrypted_private_key=encrypted_private,
            algorithm="RSA-PSS-SHA256"  # Default algorithm for now
        )

        add_user_key(db, user_key)
        return public_pem, encrypted_private

    @staticmethod
    def get_user_key_pair(db: Session, user_id: uuid.UUID) -> UserKey:
        """Get a user's key pair.

        Args:
            db: Database session.
            user_id: The user's UUID.

        Returns:
            The UserKey object.

        Raises:
            NotFoundError: If the user has no key pair.
        """
        user_key = get_by_user_id(db, user_id)
        if user_key is None:
            raise NotFoundError(f"User {user_id} has no key pair configured")

        return user_key

    @staticmethod
    def sign_record(
        db: Session,
        record_id: uuid.UUID,
        user_id: uuid.UUID,
        record_content: str
    ) -> None:
        """Sign a medical record with a user's private key.

        Args:
            db: Database session.
            record_id: The record's UUID.
            user_id: The signer's user ID.
            record_content: The record content to sign (plaintext).
        """
        user_key = get_by_user_id(db, user_id)
        if user_key is None:
            # Auto-generate key pair if not configured
            public_pem, encrypted_private = keys.generate_clinician_key_pair()
            user_key = UserKey(
                user_id=user_id,
                public_key=public_pem,
                encrypted_private_key=encrypted_private,
                algorithm="RSA-PSS-SHA256"
            )
            add_user_key(db, user_key)
            db.flush()

        # Decrypt private key from stored encrypted format
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        from app.crypto.keys import _get_master_key, decrypt_private_key_from_storage

        master_key = _get_master_key()
        decrypted_pem = decrypt_private_key_from_storage(
            user_key.encrypted_private_key,
            master_key
        )

        private_key = serialization.load_pem_private_key(
            decrypted_pem,
            password=None,
            backend=default_backend()
        )

        # Compute hash and sign
        import base64
        import hashlib

        record_hash = hashlib.sha256(record_content.encode('utf-8')).digest()

        # Sign using the appropriate algorithm
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        if user_key.algorithm == "RSA-PSS-SHA256":
            # The original code attempted to reference `keys.rsa.RSAPrivateKey`,
            # which does not exist. The correct class is `rsa.RSAPrivateKey`
            # from `cryptography.hazmat.primitives.asymmetric.rsa`.
            from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa

            if not isinstance(private_key, crypto_rsa.RSAPrivateKey):
                raise CryptoError("RSA algorithm requires RSA private key")

            signature = private_key.sign(
                record_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
        else:
            raise CryptoError(f"Unsupported algorithm: {user_key.algorithm}")

        # Store signature
        from app.models.signature import Signature
        from app.repositories.signatures_repository import add as add_signature

        db_signature = Signature(
            record_id=record_id,
            signer_id=user_id,
            signature=base64.b64encode(signature).decode('ascii'),
            algorithm=user_key.algorithm
        )

        add_signature(db, db_signature)