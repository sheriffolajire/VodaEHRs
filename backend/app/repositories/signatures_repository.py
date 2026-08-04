"""Repository for signature management.

This module provides CRUD operations for digital signatures on medical records,
enabling verification of record authenticity and integrity.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.signature import Signature


def get_by_record_id(db: Session, record_id: uuid.UUID) -> list[Signature]:
    """Get all signatures on a record.

    Args:
        db: Database session.
        record_id: The record's UUID.

    Returns:
        List of Signature objects for the record.
    """
    return (
        db.query(Signature)
        .filter(Signature.record_id == record_id)
        .order_by(Signature.created_at.asc())
        .all()
    )


def get_by_signer_id(db: Session, signer_id: uuid.UUID) -> list[Signature]:
    """Get all signatures by a specific signer.

    Args:
        db: Database session.
        signer_id: The signer's UUID.

    Returns:
        List of Signature objects created by the signer.
    """
    return (
        db.query(Signature)
        .filter(Signature.signer_id == signer_id)
        .order_by(Signature.created_at.asc())
        .all()
    )


def get_by_id(db: Session, signature_id: uuid.UUID) -> Signature | None:
    """Get a signature by its ID.

    Args:
        db: Database session.
        signature_id: The signature's UUID.

    Returns:
        The Signature object if found, None otherwise.
    """
    return db.query(Signature).filter(Signature.id == signature_id).first()


def add(db: Session, signature: Signature) -> Signature:
    """Add a new signature to a record.

    Args:
        db: Database session.
        signature: The Signature object to add.

    Returns:
        The added Signature with all attributes populated.
    """
    db.add(signature)
    db.commit()
    db.refresh(signature)
    return signature


def add_many(db: Session, signatures: list[Signature]) -> list[Signature]:
    """Add multiple signatures at once.

    Args:
        db: Database session.
        signatures: List of Signature objects to add.

    Returns:
        List of added Signature objects.
    """
    db.add_all(signatures)
    db.commit()
    for sig in signatures:
        db.refresh(sig)
    return signatures


def delete(db: Session, signature_id: uuid.UUID) -> bool:
    """Delete a signature.

    Args:
        db: Database session.
        signature_id: The signature's UUID.

    Returns:
        True if a signature was deleted, False if not found.
    """
    result = db.query(Signature).filter(Signature.id == signature_id).delete()
    db.commit()
    return result > 0