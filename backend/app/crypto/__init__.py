"""Cryptography and security utilities for Voda EHRs.

This package provides:
- Password hashing (Argon2id)
- JWT token creation/validation
- AES-256-GCM encryption for records
- RSA/ECC key management with envelope encryption
- Digital signatures for record integrity
"""
from app.crypto.encryption import (
    decrypt_data,
    decrypt_data_b64,
    encrypt_data,
    encrypt_data_b64,
    generate_aes_key,
    generate_nonce,
)
from app.crypto.hashing import hash_password, verify_password
from app.crypto.jwt import create_jwt_token, decode_jwt_token, verify_jwt_token
from app.crypto.keys import (
    KEY_ALGORITHM_ECDSA_P256_SHA256,
    KEY_ALGORITHM_RSA_PSS_SHA256,
    generate_clinician_key_pair,
    generate_institutional_key_pair,
    get_institutional_private_key,
    get_institutional_public_key,
    unwrap_aes_key_with_institutional_private,
    wrap_aes_key_with_institutional_public,
)
from app.crypto.signatures import (
    compute_record_hash,
    sign_record,
    sign_record_hash,
    verify_record_signature,
    verify_record_with_base64_sig,
    verify_signature,
)
from app.crypto.tokens import generate_password_reset_token

__all__ = [
    # Password hashing
    "hash_password",
    "verify_password",
    # JWT
    "create_jwt_token",
    "decode_jwt_token",
    "verify_jwt_token",
    # Token generation
    "generate_password_reset_token",
    # Encryption
    "encrypt_data",
    "decrypt_data",
    "encrypt_data_b64",
    "decrypt_data_b64",
    "generate_aes_key",
    "generate_nonce",
    # Key management
    "get_institutional_private_key",
    "get_institutional_public_key",
    "wrap_aes_key_with_institutional_public",
    "unwrap_aes_key_with_institutional_private",
    "generate_institutional_key_pair",
    "generate_clinician_key_pair",
    "KEY_ALGORITHM_RSA_PSS_SHA256",
    "KEY_ALGORITHM_ECDSA_P256_SHA256",
    # Signatures
    "compute_record_hash",
    "sign_record_hash",
    "verify_signature",
    "sign_record",
    "verify_record_signature",
    "verify_record_with_base64_sig",
]