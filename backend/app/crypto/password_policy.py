"""Password policy enforcement.

Security-hardened password requirements following NIST guidelines.
"""

import re

MIN_PASSWORD_LENGTH = 12


class PasswordPolicyError(ValueError):
    """Raised when a candidate password fails the policy."""


def validate_password(password: str) -> None:
    """Validate a password against the hardened security policy.
    
    Requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns (sequential, repeated)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    
    if not any(character.isupper() for character in password):
        raise PasswordPolicyError("Password must contain at least one uppercase letter.")
    
    if not any(character.islower() for character in password):
        raise PasswordPolicyError("Password must contain at least one lowercase letter.")
    
    if not any(character.isdigit() for character in password):
        raise PasswordPolicyError("Password must contain at least one number.")
    
    if not any(not character.isalnum() for character in password):
        raise PasswordPolicyError("Password must contain at least one special character (e.g., !@#$%^&*).")
    
    # Check for common weak patterns
    if re.search(r'(.)\1{2,}', password):  # 3+ repeated characters
        raise PasswordPolicyError("Password cannot contain 3 or more repeated characters.")
    
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        raise PasswordPolicyError("Password cannot contain sequential characters (e.g., '123', 'abc').")
