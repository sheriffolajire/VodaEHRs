"""Opaque token hashing for refresh and password-reset tokens.

Refresh and reset tokens are high-entropy random strings, so a fast one-way
hash is sufficient and appropriate here. Argon2id is reserved for passwords,
which are low-entropy and need deliberate slowness.
"""

import hashlib
import secrets


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest used to store a token safely."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_password_reset_token() -> str:
    """Generate a secure random password reset token.

    Returns:
        A 32-character URL-safe token string.
    """
    return secrets.token_urlsafe(32)


def verify_password_reset_token_stored(stored_hash: str, token: str) -> bool:
    """Verify a password reset token against its stored hash.

    Args:
        stored_hash: The SHA-256 hash stored in the database.
        token: The plaintext token to verify.

    Returns:
        True if the token matches the hash.
    """
    computed_hash = hash_token(token)
    return secrets.compare_digest(stored_hash, computed_hash)
