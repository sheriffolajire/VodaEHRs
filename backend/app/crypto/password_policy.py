"""Password policy enforcement.

Kept intentionally simple and readable: a small set of clear rules rather than a
configurable engine. Tightened later if the project requires it.
"""

MIN_PASSWORD_LENGTH = 8


class PasswordPolicyError(ValueError):
    """Raised when a candidate password fails the policy."""


def validate_password(password: str) -> None:
    """Validate a password against the policy, raising on the first violation."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if not any(character.isalpha() for character in password):
        raise PasswordPolicyError("Password must contain at least one letter.")
    if not any(character.isdigit() for character in password):
        raise PasswordPolicyError("Password must contain at least one number.")
