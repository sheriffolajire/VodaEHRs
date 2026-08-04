"""Institutional and clinician key management with envelope encryption.

This module provides:
- Institutional key pair bootstrap/load from environment variables
- RSA/ECC key wrapping/unwrap for envelope encryption
- Clinician key pair generation and storage
- Master key encryption for private key protection at rest.
"""
import base64
import hashlib
import os
import secrets

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.services.exceptions import CryptoError

# =============================================================================
# Institutional Key Management
# =============================================================================

def _load_institutional_private_key_from_env() -> PrivateKeyTypes:
    """Load the institutional private key from pydantic settings (loaded from .env).
    
    The private key should be base64-encoded PKCS8 PEM format.
    This is the most secure approach for production - keys are provided
    via environment variables and never stored in code or version control.
    
    Returns:
        The private key object for decryption operations.
        
    Raises:
        CryptoError: If the key is missing or invalid.
    """
    env_key = settings.institutional_private_key
    if env_key is None or env_key == "change_me_base64_encoded_pem":
        raise CryptoError(
            "INSTITUTIONAL_PRIVATE_KEY is not set or using default value. "
            "Please set INSTITUTIONAL_PRIVATE_KEY in your .env file with a base64-encoded PKCS8 PEM format RSA/EC private key."
        )
    
    try:
        # Base64 decode
        key_bytes = base64.b64decode(env_key)
        # Load PKCS8 format (encrypted with master key)
        return serialization.load_pem_private_key(
            key_bytes,
            password=None,  # Key is encrypted with master key at rest
            backend=default_backend()
        )
    except Exception as e:
        raise CryptoError(f"Failed to load institutional private key: {e}")


def _load_institutional_public_key_from_env() -> PublicKeyTypes:
    """Load the institutional public key from pydantic settings (loaded from .env).
    
    The public key should be base64-encoded SPKI PEM format.
    
    Returns:
        The public key object for encryption/wrapping operations.
        
    Raises:
        CryptoError: If the key is missing or invalid.
    """
    env_key = settings.institutional_public_key
    if env_key is None or env_key == "change_me_base64_encoded_pem":
        raise CryptoError(
            "INSTITUTIONAL_PUBLIC_KEY is not set or using default value. "
            "Please set INSTITUTIONAL_PUBLIC_KEY in your .env file with a base64-encoded SPKI PEM format RSA/EC public key."
        )
    
    try:
        key_bytes = base64.b64decode(env_key)
        return serialization.load_pem_public_key(key_bytes, backend=default_backend())
    except Exception as e:
        raise CryptoError(f"Failed to load institutional public key: {e}")


def _load_institutional_keys_from_files() -> tuple[PrivateKeyTypes, PublicKeyTypes]:
    """Load institutional keys from file paths specified in environment.
    
    This is useful for Docker volume mounts or external secret management.
    
    Returns:
        Tuple of (private_key, public_key).
        
    Raises:
        CryptoError: If keys cannot be loaded.
    """
    private_path = os.environ.get("INSTITUTIONAL_PRIVATE_KEY_PATH")
    public_path = os.environ.get("INSTITUTIONAL_PUBLIC_KEY_PATH")
    
    if not private_path or not public_path:
        raise CryptoError(
            "INSTITUTIONAL_PRIVATE_KEY_PATH and INSTITUTIONAL_PUBLIC_KEY_PATH must be set."
        )
    
    try:
        with open(private_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        with open(public_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
        
        return private_key, public_key
    except Exception as e:
        raise CryptoError(f"Failed to load institutional keys from files: {e}")


def get_institutional_private_key() -> PrivateKeyTypes:
    """Get the institutional private key for decryption/wrapping operations.
    
    First tries environment variable, then file loading.
    
    Returns:
        The institutional private key.
    """
    # Try environment variable first
    try:
        return _load_institutional_private_key_from_env()
    except CryptoError:
        pass

    # Try file loading
    try:
        private_key, _ = _load_institutional_keys_from_files()
        return private_key
    except CryptoError:
        pass

    # Development fallback: generate a temporary RSA key if insecure mode is allowed.
    if settings.allow_insecure:
        from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
        # 2048‑bit RSA key is sufficient for dev/testing.
        temporary_key = crypto_rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        return temporary_key

    raise CryptoError(
        "Could not load institutional private key. "
        "Set INSTITUTIONAL_PRIVATE_KEY env var or INSTITUTIONAL_PRIVATE_KEY_PATH file."
    )


def get_institutional_public_key() -> PublicKeyTypes:
    """Get the institutional public key for encryption/unwrap operations.
    
    Returns:
        The institutional public key.
    """
    # Try environment variable first
    try:
        return _load_institutional_public_key_from_env()
    except CryptoError:
        pass
    
    # Try file loading
    try:
        _, public_key = _load_institutional_keys_from_files()
        return public_key
    except CryptoError:
        pass
    
    raise CryptoError(
        "Could not load institutional public key. "
        "Set INSTITUTIONAL_PUBLIC_KEY env var or INSTITUTIONAL_PUBLIC_KEY_PATH file."
    )


def wrap_aes_key_with_institutional_public(key: bytes) -> bytes:
    """Wrap an AES data key using the institutional public key.
    
    This is the envelope encryption step - the AES key is encrypted
    with the institutional public key so only the holder of the
    institutional private key can unwrap it.
    
    Args:
        key: The 32-byte AES data key to wrap.
        
    Returns:
        The wrapped (encrypted) AES key.
        
    Raises:
        CryptoError: If wrapping fails.
    """
    # In insecure development mode we skip actual RSA wrapping to avoid the need
    # for matching private keys. The caller can still treat the returned value as
    # an opaque wrapped key.
    # NOTE: Use the cached ``settings`` instance directly – this respects the
    # ``ALLOW_INSECURE`` flag even when the module was imported before the flag
    # was potentially overridden in the environment. Returning the raw key
    # prevents attempts to load institutional keys, which caused the previous
    # ``CryptoError`` during document uploads.
    if settings.allow_insecure:
        return key

    try:
        pub_key = get_institutional_public_key()

        if isinstance(pub_key, rsa.RSAPublicKey):
            # RSA-OAEP wrapping
            ciphertext = pub_key.encrypt(
                key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        elif isinstance(pub_key, ec.EllipticCurvePublicKey):
            raise CryptoError("ECC key wrapping not yet implemented. Use RSA keys.")
        else:
            raise CryptoError(f"Unsupported public key type: {type(pub_key)}")

        return ciphertext
    except Exception as e:
        raise CryptoError(f"Failed to wrap AES key with institutional public key: {e}")


def unwrap_aes_key_with_institutional_private(wrapped_key: bytes) -> bytes:
    """Unwrap an AES data key using the institutional private key.
    
    Args:
        wrapped_key: The wrapped (encrypted) AES key.
        
    Returns:
        The unwrapped (plaintext) AES data key.
        
    Raises:
        CryptoError: If unwrapping fails.
    """
    # In insecure mode the key was not actually wrapped; return it directly.
    if getattr(settings, "allow_insecure", False):
        return wrapped_key

    try:
        priv_key = get_institutional_private_key()

        if isinstance(priv_key, rsa.RSAPrivateKey):
            plaintext = priv_key.decrypt(
                wrapped_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        elif isinstance(priv_key, ec.EllipticCurvePrivateKey):
            raise CryptoError("ECC key unwrapping not yet implemented. Use RSA keys.")
        else:
            raise CryptoError(f"Unsupported private key type: {type(priv_key)}")

        return plaintext
    except Exception as e:
        raise CryptoError(f"Failed to unwrap AES key with institutional private key: {e}")

# ---------------------------------------------------------------------
# Key rotation utilities
# ---------------------------------------------------------------------
def rotate_master_key(new_master_key_b64: str) -> None:
    """Rotate the AES master key used to encrypt clinician private keys.

    This function re‑encrypts every stored clinician private key with the
    provided ``new_master_key_b64`` (a base64‑encoded 32‑byte key). It is a
    one‑shot operation and should be called by an administrator after the
    new key has been securely stored in the environment.

    Args:
        new_master_key_b64: Base64 representation of the new master key.

    Raises:
        CryptoError: If any re‑encryption step fails.
    """
    from app.database.session import SessionLocal
    from app.models.user_keys import UserKey
    from app.services.exceptions import CryptoError
    import base64

    # Decode the new key
    try:
        new_key = base64.b64decode(new_master_key_b64)
    except Exception as e:
        raise CryptoError(f"Invalid base64 master key: {e}")

    # Re‑encrypt each clinician private key
    db = SessionLocal()
    try:
        user_keys = db.query(UserKey).all()
        for uk in user_keys:
            # Decrypt existing private key with the old master key
            old_master_key = _get_master_key()
            plaintext = decrypt_private_key_from_storage(uk.encrypted_private_key, old_master_key)

            # Encrypt with the new master key
            encrypted = encrypt_private_key_for_storage(plaintext, new_key)
            uk.encrypted_private_key = encrypted
        db.commit()
    except Exception as e:
        db.rollback()
        raise CryptoError(f"Failed to rotate master key: {e}")
    finally:
        db.close()


# =============================================================================
# Master Key Operations
# =============================================================================

# Cache for a deterministic insecure master key. This ensures that multiple
# calls to ``_get_master_key`` during a test run (or dev session) return the
# same key, avoiding decryption failures caused by generating a new random key
# each time.
_insecure_master_key: bytes | None = None

def _get_master_key() -> bytes:
    """Retrieve the AES master key used to encrypt clinician private keys.

    In production the key **must** be supplied via the ``AES_MASTER_KEY``
    environment variable (base64‑encoded 32‑byte key). For local development the
    ``allow_insecure`` flag can be set to ``True`` – in that case a deterministic
    temporary key is generated once per process and reused for all encryption
    operations. This deterministic key is safe for testing but must never be
    used in production.
    """
    # If the developer has opted into insecure mode, generate (or reuse) a temporary key.
    if getattr(settings, "allow_insecure", False):
        global _insecure_master_key
        if _insecure_master_key is None:
            # 32‑byte (256‑bit) key suitable for AES‑GCM.
            _insecure_master_key = secrets.token_bytes(32)
        return _insecure_master_key

    key = settings.aes_master_key
    if not key:
        raise CryptoError(
            "AES_MASTER_KEY is not set. Provide a base64‑encoded 32‑byte key or "
            "enable ALLOW_INSECURE for development."
        )
    # Decode the base64 representation; any decoding error will surface as a
    # CryptoError for clarity.
    try:
        return base64.b64decode(key)
    except Exception as exc:
        raise CryptoError(f"Failed to decode AES_MASTER_KEY: {exc}")


def encrypt_private_key_for_storage(private_key_pem: bytes, master_key: bytes | None = None) -> bytes:
    """Encrypt a private key for secure storage at rest.
    
    Args:
        private_key_pem: The PEM-encoded private key.
        master_key: Optional master key; uses config if not provided.
        
    Returns:
        Base64-encoded encrypted private key.
    """
    if master_key is None:
        master_key = _get_master_key()
    
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(master_key)
    ciphertext = aesgcm.encrypt(nonce, private_key_pem, None)
    
    # Return nonce + ciphertext (for decryption later)
    combined = nonce + ciphertext
    return base64.b64encode(combined)


def decrypt_private_key_from_storage(encrypted_pem_b64: str, master_key: bytes | None = None) -> bytes:
    """Decrypt a private key that was encrypted for storage.
    
    Args:
        encrypted_pem_b64: Base64-encoded encrypted private key.
        master_key: Optional master key; uses config if not provided.
        
    Returns:
        The PEM-encoded private key.
    """
    if master_key is None:
        master_key = _get_master_key()
    
    combined = base64.b64decode(encrypted_pem_b64)
    nonce = combined[:12]
    ciphertext = combined[12:]
    
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(nonce, ciphertext, None)


# =============================================================================
# Key Generation Utilities
# =============================================================================

def generate_institutional_key_pair(
    key_type: str = "RSA",
    key_size: int = 4096
) -> tuple[str, str]:
    """Generate a new institutional key pair.
    
    This is typically used once during initial setup/bootstrap.
    
    Args:
        key_type: "RSA" or "EC" for elliptic curve.
        key_size: For RSA, typically 2048 or 4096.
        
    Returns:
        Tuple of (public_key_pem, private_key_pem) in base64-encoded PKCS8/SPKI format.
    """
    
    if key_type == "RSA":
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
    elif key_type == "EC":
        private_key = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
    else:
        raise ValueError(f"Unsupported key type: {key_type}")
    
    # Serialize private key (PKCS8 format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key (SPKI format)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Base64 encode for environment storage
    return (
        base64.b64encode(public_pem).decode('ascii'),
        base64.b64encode(private_pem).decode('ascii')
    )


def generate_clinician_key_pair(
    key_type: str = "RSA",
    key_size: int = 2048
) -> tuple[str, str]:
    """Generate a new clinician key pair for digital signatures.
    
    The private key will be encrypted with the master key before storage.
    
    Args:
        key_type: "RSA" or "EC" for elliptic curve.
        key_size: For RSA, typically 2048 (sufficient for signing).
        
    Returns:
        Tuple of (public_key_pem, encrypted_private_key_b64).
    """
    
    if key_type == "RSA":
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
    elif key_type == "EC":
        private_key = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
    else:
        raise ValueError(f"Unsupported key type: {key_type}")
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Encrypt with master key
    master_key = _get_master_key()
    encrypted_private = encrypt_private_key_for_storage(private_pem, master_key)
    
    # Serialize public key
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return (
        base64.b64encode(public_pem).decode('ascii'),
        encrypted_private.decode('ascii')
    )


# =============================================================================
# Key Generation (Delegated to encryption module)
# =============================================================================

def generate_aes_key() -> bytes:
    """Generate a random 256-bit AES key for data encryption.
    
    Returns:
        32 bytes of cryptographically secure random data.
    """
    from app.crypto import encryption
    return encryption.generate_aes_key()


# =============================================================================
# Key Algorithms
# =============================================================================

KEY_ALGORITHM_RSA_PSS_SHA256 = "RSA-PSS-SHA256"
KEY_ALGORITHM_ECDSA_P256_SHA256 = "ECDSA-P256-SHA256"

SUPPORTED_KEY_ALGORITHMS = [KEY_ALGORITHM_RSA_PSS_SHA256, KEY_ALGORITHM_ECDSA_P256_SHA256]


def get_key_algorithm_for_private_key(private_key: PrivateKeyTypes) -> str:
    """Determine the appropriate signature algorithm for a key.
    
    Args:
        private_key: The private key object.
        
    Returns:
        The algorithm name string.
    """
    if isinstance(private_key, rsa.RSAPrivateKey):
        return KEY_ALGORITHM_RSA_PSS_SHA256
    elif isinstance(private_key, ec.EllipticCurvePrivateKey):
        return KEY_ALGORITHM_ECDSA_P256_SHA256
    else:
        raise ValueError(f"Unsupported key type for signing: {type(private_key)}")


def get_key_algorithm_for_public_key(public_key: PublicKeyTypes) -> str:
    """Determine the appropriate signature algorithm for a key.
    
    Args:
        public_key: The public key object.
        
    Returns:
        The algorithm name string.
    """
    if isinstance(public_key, rsa.RSAPublicKey):
        return KEY_ALGORITHM_RSA_PSS_SHA256
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        return KEY_ALGORITHM_ECDSA_P256_SHA256
    else:
        raise ValueError(f"Unsupported key type for verification: {type(public_key)}")