"""Repository for nursing tasks persistence."""
import uuid
from datetime import datetime, UTC
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.nursing_task import NursingTask, TaskStatus, TaskPriority, TaskType


def get_by_id(db: Session, task_id: uuid.UUID) -> NursingTask | None:
    """Get a task by ID."""
    return db.get(NursingTask, task_id)


def list_for_nurse(
    db: Session,
    nurse_id: uuid.UUID,
    status: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> List[NursingTask]:
    """List tasks assigned to a nurse."""
    statement = select(NursingTask).where(NursingTask.assigned_to == nurse_id)
    
    if status:
        # Compare using the enum's stored value (lower‑case string) to avoid
        # mismatches between the Python enum name (e.g. "PENDING") and the
        # PostgreSQL enum values (e.g. "pending").
        statement = statement.where(NursingTask.status == status.value)
    
    statement = (
        statement
        .order_by(NursingTask.priority.desc(), NursingTask.due_date.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


def list_for_patient(
    db: Session,
    patient_id: uuid.UUID,
    status: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> List[NursingTask]:
    """List tasks for a patient."""
    statement = select(NursingTask).where(NursingTask.patient_id == patient_id)
    
    if status:
        statement = statement.where(NursingTask.status == status.value)
    
    statement = (
        statement
        .order_by(NursingTask.priority.desc(), NursingTask.due_date.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


def list_pending_for_nurse(
    db: Session,
    nurse_id: uuid.UUID,
    limit: int = 100
) -> List[NursingTask]:
    """List pending tasks for a nurse, ordered by priority and due date."""
    statement = (
        select(NursingTask)
        .where(
            and_(
                NursingTask.assigned_to == nurse_id,
                NursingTask.status.in_([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value])
            )
        )
        .order_by(NursingTask.priority.desc(), NursingTask.due_date.asc())
        .limit(limit)
    )
    return list(db.scalars(statement))


def count_pending_for_nurse(db: Session, nurse_id: uuid.UUID) -> int:
    """Count pending tasks for a nurse."""
    return (
        db.query(NursingTask)
        .filter(
            and_(
                NursingTask.assigned_to == nurse_id,
                NursingTask.status.in_([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value])
            )
        )
        .count()
    )


def count_vitals_due_for_nurse(db: Session, nurse_id: uuid.UUID) -> int:
    """Count vitals tasks due for a nurse."""
    return (
        db.query(NursingTask)
        .filter(
            and_(
                NursingTask.assigned_to == nurse_id,
                NursingTask.task_type == TaskType.VITALS,
                NursingTask.status.in_([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value])
            )
        )
        .count()
    )


def add(db: Session, task: NursingTask) -> NursingTask:
    """Add a new task."""
    db.add(task)
    db.flush()
    return task


def update(db: Session, task: NursingTask) -> NursingTask:
    """Update a task."""
    db.flush()
    return task


def delete(db: Session, task_id: uuid.UUID) -> bool:
    """Delete a task."""
    task = get_by_id(db, task_id)
    if task:
        db.delete(task)
        return True
    return False
