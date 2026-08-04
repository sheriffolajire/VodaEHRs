"""Persistence for medical document metadata."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.medical_document import MedicalDocument


def get_by_id(db: Session, document_id: uuid.UUID) -> MedicalDocument | None:
    return db.get(MedicalDocument, document_id)


def list_for_patient(db: Session, patient_id: uuid.UUID) -> list[MedicalDocument]:
    return list(
        db.scalars(
            select(MedicalDocument)
            .where(MedicalDocument.patient_id == patient_id)
            .order_by(MedicalDocument.uploaded_at.desc())
        )
    )


def add(db: Session, document: MedicalDocument) -> MedicalDocument:
    db.add(document)
    db.flush()
    return document
