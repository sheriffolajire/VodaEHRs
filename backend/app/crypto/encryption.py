"""AES-256-GCM encryption service for medical records.

This module provides symmetric encryption/decryption using AES-256-GCM
with authenticated encryption (confidentiality + integrity).

The encrypted data keys are then wrapped with the institutional RSA/ECC
key pair for envelope encryption.
"""
import base64
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.exceptions import CryptoError


def generate_aes_key() -> bytes:
    """Generate a random 256-bit AES key.
    
    Returns:
        32 bytes of cryptographically secure random data.
    """
    return secrets.token_bytes(32)


def generate_nonce() -> bytes:
    """Generate a random nonce for AES-GCM.
    
    The nonce must be unique for each encryption operation with the same key.
    96 bits (12 bytes) is the recommended size for GCM mode.
    
    Returns:
        12 bytes of cryptographically secure random data.
    """
    return secrets.token_bytes(12)


def encrypt_data(data: bytes, key: bytes) -> tuple[bytes, bytes, bytes]:
    """Encrypt data using AES-256-GCM.
    
    Args:
        data: The plaintext data to encrypt.
        key: The 32-byte AES key.
        
    Returns:
        A tuple of (ciphertext, nonce, auth_tag) where:
        - ciphertext: The encrypted data
        - nonce: The 12-byte nonce used for encryption
        - auth_tag: The 16-byte authentication tag
        
    Raises:
        CryptoError: If encryption fails.
    """
    try:
        nonce = generate_nonce()
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # For GCM, the authentication tag is appended to the ciphertext
        # We need to extract it (last 16 bytes)
        auth_tag = ciphertext[-16:]
        actual_ciphertext = ciphertext[:-16]
        return actual_ciphertext, nonce, auth_tag
    except Exception as e:
        raise CryptoError(f"AES-GCM encryption failed: {e}")


def decrypt_data(ciphertext: bytes, nonce: bytes, auth_tag: bytes, key: bytes) -> bytes:
    """Decrypt data using AES-256-GCM.
    
    Args:
        ciphertext: The encrypted data (without auth tag).
        nonce: The 12-byte nonce used for encryption.
        auth_tag: The 16-byte authentication tag.
        key: The 32-byte AES key.
        
    Returns:
        The decrypted plaintext data.
        
    Raises:
        CryptoError: If decryption fails or authentication fails (tampering detected).
    """
    try:
        aesgcm = AESGCM(key)
        # Concatenate ciphertext and auth tag for decryption
        ciphertext_with_tag = ciphertext + auth_tag
        return aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    except Exception as e:
        raise CryptoError(f"AES-GCM decryption failed (possible tampering): {e}")


def encrypt_data_b64(data: str, key: bytes) -> dict[str, str]:
    """Encrypt data and return base64-encoded components.
    
    This is a convenience wrapper for API use where data comes as strings.
    
    Args:
        data: The plaintext string to encrypt.
        key: The 32-byte AES key.
        
    Returns:
        A dictionary with base64-encoded values:
        - encrypted_data: Base64 encoded ciphertext
        - nonce: Base64 encoded nonce
        - auth_tag: Base64 encoded authentication tag
    """
    plaintext = data.encode('utf-8')
    ciphertext, nonce, auth_tag = encrypt_data(plaintext, key)
    
    return {
        'encrypted_data': base64.b64encode(ciphertext).decode('ascii'),
        'nonce': base64.b64encode(nonce).decode('ascii'),
        'auth_tag': base64.b64encode(auth_tag).decode('ascii'),
    }


def decrypt_data_b64(encrypted_data: str, nonce: str, auth_tag: str, key: bytes) -> str:
    """Decrypt base64-encoded data and return string.
    
    Args:
        encrypted_data: Base64 encoded ciphertext.
        nonce: Base64 encoded nonce.
        auth_tag: Base64 encoded authentication tag.
        key: The 32-byte AES key.
        
    Returns:
        The decrypted plaintext string.
    """
    ciphertext = base64.b64decode(encrypted_data)
    nonce_bytes = base64.b64decode(nonce)
    auth_tag_bytes = base64.b64decode(auth_tag)
    
    plaintext = decrypt_data(ciphertext, nonce_bytes, auth_tag_bytes, key)
    return plaintext.decode('utf-8')