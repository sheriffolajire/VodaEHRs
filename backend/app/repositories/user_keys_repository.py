"""Repository for user key management.

This module provides CRUD operations for user key pairs used in
digital signature and encryption operations.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.user_keys import UserKey


def get_by_user_id(db: Session, user_id: uuid.UUID) -> UserKey | None:
    """Get a user's key pair by user ID.

    Args:
        db: Database session.
        user_id: The user's UUID.

    Returns:
        The UserKey object if found, None otherwise.
    """
    return db.query(UserKey).filter(UserKey.user_id == user_id).first()


def get_by_id(db: Session, key_id: uuid.UUID) -> UserKey | None:
    """Get a user key by its ID.

    Args:
        db: Database session.
        key_id: The key's UUID.

    Returns:
        The UserKey object if found, None otherwise.
    """
    return db.query(UserKey).filter(UserKey.id == key_id).first()


def add(db: Session, user_key: UserKey) -> UserKey:
    """Add a new user key pair.

    Args:
        db: Database session.
        user_key: The UserKey object to add.

    Returns:
        The added UserKey with all attributes populated.
    """
    db.add(user_key)
    db.commit()
    db.refresh(user_key)
    return user_key


def delete(db: Session, user_id: uuid.UUID) -> bool:
    """Delete a user's key pair.

    Args:
        db: Database session.
        user_id: The user's UUID.

    Returns:
        True if a key was deleted, False if no key existed.
    """
    result = db.query(UserKey).filter(UserKey.user_id == user_id).delete()
    db.commit()
    return result > 0