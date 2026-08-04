"""Digital signature service for medical record integrity.

This module provides digital signature creation and verification using
RSA-PSS or ECDSA algorithms over SHA-256 hashes.

Signatures are created by authoring clinicians to prove:
- Authenticity: The record was indeed created by the claimed clinician
- Non-repudiation: The clinician cannot deny having created the record
- Integrity: Any modification to the record would invalidate the signature
"""
import hashlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes

from app.crypto.keys import (
    KEY_ALGORITHM_ECDSA_P256_SHA256,
    KEY_ALGORITHM_RSA_PSS_SHA256,
    get_key_algorithm_for_private_key,
    get_key_algorithm_for_public_key,
)
from app.services.exceptions import CryptoError


def compute_record_hash(content: str) -> bytes:
    """Compute SHA-256 hash of record content.
    
    This hash is what gets signed - the signature protects the exact content.
    
    Args:
        content: The record content to hash.
        
    Returns:
        The 32-byte SHA-256 hash of the content.
    """
    return hashlib.sha256(content.encode('utf-8')).digest()


def sign_record_hash(
    record_hash: bytes,
    private_key: PrivateKeyTypes,
    algorithm: str | None = None
) -> bytes:
    """Sign a record hash with a private key.
    
    Args:
        record_hash: The SHA-256 hash of the record content.
        private_key: The private key to sign with.
        algorithm: Optional algorithm override; auto-detects if None.
        
    Returns:
        The signature bytes.
        
    Raises:
        CryptoError: If signing fails.
    """
    try:
        if algorithm is None:
            algorithm = get_key_algorithm_for_private_key(private_key)
        
        if algorithm == KEY_ALGORITHM_RSA_PSS_SHA256:
            if not isinstance(private_key, rsa.RSAPrivateKey):
                raise CryptoError("RSA-PSS-SHA256 algorithm requires RSA private key")
            
            signature = private_key.sign(
                record_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        
        elif algorithm == KEY_ALGORITHM_ECDSA_P256_SHA256:
            if not isinstance(private_key, ec.EllipticCurvePrivateKey):
                raise CryptoError("ECDSA-P256-SHA256 algorithm requires EC private key")
            
            signature = private_key.sign(
                record_hash,
                ec.ECDSA(hashes.SHA256())
            )
        
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return signature
    
    except Exception as e:
        raise CryptoError(f"Failed to sign record: {e}")


def verify_signature(
    record_hash: bytes,
    signature: bytes,
    public_key: PublicKeyTypes,
    algorithm: str | None = None
) -> bool:
    """Verify a signature against a record hash.
    
    Args:
        record_hash: The expected SHA-256 hash of the record content.
        signature: The signature bytes to verify.
        public_key: The public key to verify with.
        algorithm: Optional algorithm override; auto-detects if None.
        
    Returns:
        True if the signature is valid and matches the hash.
        
    Raises:
        CryptoError: If verification fails (not necessarily invalid - could be key issues).
    """
    try:
        if algorithm is None:
            algorithm = get_key_algorithm_for_public_key(public_key)
        
        if algorithm == KEY_ALGORITHM_RSA_PSS_SHA256:
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise CryptoError("RSA-PSS-SHA256 algorithm requires RSA public key")
            
            # Use the same padding parameters as the signing operation.
            # The original code used `padding.PSS.AUTO`, which can cause
            # verification failures when the signer used `MAX_LENGTH`. We now
            # enforce `MAX_LENGTH` for consistency.
            public_key.verify(
                signature,
                record_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        
        elif algorithm == KEY_ALGORITHM_ECDSA_P256_SHA256:
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise CryptoError("ECDSA-P256-SHA256 algorithm requires EC public key")
            
            public_key.verify(
                signature,
                record_hash,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    except Exception:
        # Signature verification failed - could be invalid signature or key issue
        return False


def sign_record(content: str, private_key: PrivateKeyTypes) -> dict:
    """Sign a complete record.
    
    Convenience function that computes hash and creates signature.
    
    Args:
        content: The record content to sign.
        private_key: The private key to sign with.
        
    Returns:
        Dictionary with:
        - hash: Base64-encoded SHA-256 hash
        - signature: Base64-encoded signature
        - algorithm: The algorithm used
    """
    record_hash = compute_record_hash(content)
    signature = sign_record_hash(record_hash, private_key)
    algorithm = get_key_algorithm_for_private_key(private_key)
    
    import base64
    
    return {
        'hash': base64.b64encode(record_hash).decode('ascii'),
        'signature': base64.b64encode(signature).decode('ascii'),
        'algorithm': algorithm,
    }


def verify_record_signature(content: str, signature: bytes, public_key: PublicKeyTypes, algorithm: str) -> bool:
    """Verify a record's signature.
    
    Args:
        content: The record content to verify.
        signature: The signature bytes.
        public_key: The public key to verify with.
        algorithm: The algorithm that was used (e.g., RSA-PSS-SHA256).
        
    Returns:
        True if the signature is valid.
    """
    record_hash = compute_record_hash(content)
    return verify_signature(record_hash, signature, public_key, algorithm)


def verify_record_with_base64_sig(
    content: str,
    signature_b64: str,
    public_key: PublicKeyTypes,
    algorithm: str
) -> bool:
    """Verify a record's signature from base64-encoded signature.
    
    Args:
        content: The record content to verify.
        signature_b64: Base64-encoded signature.
        public_key: The public key to verify with.
        algorithm: The algorithm that was used.
        
    Returns:
        True if the signature is valid.
    """
    import base64
    signature = base64.b64decode(signature_b64)
    return verify_record_signature(content, signature, public_key, algorithm)