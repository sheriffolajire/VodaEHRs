"""Persistence for user accounts."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role, RoleName
from app.models.user import User, UserStatus


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)))


def list_clinicians(db: Session) -> list[User]:
    """Return active doctors and nurses, ordered by name.

    Used by registrars/schedulers to pick a clinician without exposing the full
    user directory.
    """
    return list(
        db.scalars(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(
                Role.name.in_((RoleName.DOCTOR, RoleName.NURSE)),
                User.status == UserStatus.ACTIVE,
            )
            .order_by(User.first_name, User.last_name)
        )
    )


def add(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user
