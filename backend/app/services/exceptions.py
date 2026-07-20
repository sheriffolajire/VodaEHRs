"""Domain-level exceptions for the service layer.

Routers translate these into HTTP responses so services stay transport-agnostic.
"""


class AuthError(Exception):
    """Authentication failed (bad credentials, disabled account, invalid token)."""


class PermissionError_(Exception):
    """The caller is authenticated but not allowed to perform the action."""


class NotFoundError(Exception):
    """A requested resource does not exist."""


class ConflictError(Exception):
    """The action conflicts with existing state (e.g. duplicate email)."""


class ValidationError(Exception):
    """Input failed a business rule (e.g. password policy)."""
