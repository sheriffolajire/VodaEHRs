"""User and role management business logic (Admin-facing)."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.crypto.hashing import hash_password
from app.crypto.password_policy import PasswordPolicyError, validate_password
from app.models.role import Role, RoleName
from app.models.user import User, UserStatus
from app.repositories import role_repository, user_repository
from app.schemas.user import UserCreate, UserUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


def list_users(db: Session) -> list[User]:
    return user_repository.list_users(db)


def list_clinicians(db: Session) -> list[User]:
    return user_repository.list_clinicians(db)


def list_roles(db: Session) -> list[Role]:
    return role_repository.list_roles(db)


def _resolve_role(db: Session, name: RoleName) -> Role:
    role = role_repository.get_by_name(db, name)
    if role is None:
        # Roles are seeded during migration, so a missing role signals a setup bug.
        raise NotFoundError(f"Role '{name.value}' does not exist.")
    return role


def create_user(db: Session, payload: UserCreate, actor_id: str) -> User:
    """Create a new account, enforcing unique email and the password policy."""
    if user_repository.get_by_email(db, payload.email) is not None:
        raise ConflictError("A user with this email already exists.")

    try:
        validate_password(payload.password)
    except PasswordPolicyError as exc:
        raise ValidationError(str(exc)) from exc

    role = _resolve_role(db, payload.role)
    user = user_repository.add(
        db,
        User(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role_id=role.id,
        ),
    )
    record_event(
        AuditEvent(action="user.create", user_id=actor_id, status="success", reason=str(user.id))
    )
    return user


def update_user(db: Session, user_id: uuid.UUID, payload: UserUpdate, actor_id: str) -> User:
    """Update profile fields, role, or account status."""
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.")

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.role is not None:
        user.role_id = _resolve_role(db, payload.role).id
    if payload.status is not None:
        user.status = payload.status

    db.flush()
    record_event(
        AuditEvent(action="user.update", user_id=actor_id, status="success", reason=str(user.id))
    )
    return user


def disable_user(db: Session, user_id: uuid.UUID, actor_id: str) -> User:
    """Soft-disable an account. Accounts are never hard-deleted (audit trail)."""
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found.")

    user.status = UserStatus.DISABLED
    db.flush()
    record_event(
        AuditEvent(action="user.disable", user_id=actor_id, status="success", reason=str(user.id))
    )
    return user
