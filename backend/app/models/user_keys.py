"""User key pairs for digital signatures.

This module provides the `UserKey` model for storing clinician public and
encrypted private keys, enabling digital signature verification and decryption
operations.
"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk


class UserKey(Base):
    """User key pair for digital signatures and decryption.

    Each clinician has a key pair:
    - Public key: Stored in plaintext for signature verification
    - Private key: Encrypted with master key and stored in database

    This enables:
    - Digital signature verification on medical records
    - Secure key management while maintaining confidentiality
    """
    __tablename__ = "user_keys"

    id: Mapped[uuid.UUID] = uuid_pk()

    # FK to users.id - each user has at most one key pair
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )

    # Public key in PEM format (SPKI encoding)
    public_key: Mapped[str] = mapped_column(String)

    # Private key encrypted with master key (AES-GCM)
    # Format: base64(nonce + ciphertext)
    encrypted_private_key: Mapped[str] = mapped_column(String)

    # Algorithm identifier: "RSA-PSS-SHA256" or "ECDSA-P256-SHA256"
    algorithm: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = created_at_column()

    # Relationship to user
    user: Mapped["User"] = relationship("User", back_populates="key_pair")