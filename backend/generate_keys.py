#!/usr/bin/env python3
"""Generate new institutional keys in the correct format."""

import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_institutional_key_pair(key_size: int = 4096) -> tuple[str, str]:
    """Generate a new institutional key pair in PKCS8/SPKI format."""
    
    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    
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

def main():
    print("Generating new institutional key pair...")
    
    public_key_b64, private_key_b64 = generate_institutional_key_pair()
    
    print(f"\nPublic Key (base64, SPKI format):")
    print(public_key_b64)
    
    print(f"\nPrivate Key (base64, PKCS8 format):")
    print(private_key_b64)
    
    print(f"\nKey lengths:")
    print(f"Public key: {len(public_key_b64)} characters")
    print(f"Private key: {len(private_key_b64)} characters")
    
    # Test that they can be loaded
    print("\nTesting key loading...")
    try:
        # Test private key
        private_bytes = base64.b64decode(private_key_b64)
        private_key = serialization.load_pem_private_key(
            private_bytes,
            password=None,
            backend=default_backend()
        )
        print("✓ Private key loads successfully")
        
        # Test public key
        public_bytes = base64.b64decode(public_key_b64)
        public_key = serialization.load_pem_public_key(
            public_bytes,
            backend=default_backend()
        )
        print("✓ Public key loads successfully")
        
        print("\n✓ All keys generated and validated successfully!")
        print("\nUpdate your .env file with these values:")
        print(f"INSTITUTIONAL_PUBLIC_KEY={public_key_b64}")
        print(f"INSTITUTIONAL_PRIVATE_KEY={private_key_b64}")
        
    except Exception as e:
        print(f"✗ Failed to load generated keys: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()