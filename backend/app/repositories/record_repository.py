"""Persistence for medical records."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medical_record import MedicalRecord


def get_by_id(db: Session, record_id: uuid.UUID) -> MedicalRecord | None:
    return db.get(MedicalRecord, record_id)


def list_for_patient(db: Session, patient_id: uuid.UUID) -> list[MedicalRecord]:
    return list(
        db.scalars(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.created_at.desc())
        )
    )


def add(db: Session, record: MedicalRecord) -> MedicalRecord:
    db.add(record)
    db.flush()
    return record


def update(db: Session, record: MedicalRecord) -> MedicalRecord:
    """Update an existing record."""
    db.flush()
    db.refresh(record)
    return record
