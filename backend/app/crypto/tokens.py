"""Opaque token hashing for refresh and password-reset tokens.

Refresh and reset tokens are high-entropy random strings, so a fast one-way
hash is sufficient and appropriate here. Argon2id is reserved for passwords,
which are low-entropy and need deliberate slowness.
"""

import hashlib


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest used to store a token safely."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
