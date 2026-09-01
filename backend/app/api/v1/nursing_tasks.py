"""Nursing tasks API endpoints.

Provides endpoints for managing nursing tasks and care activities.
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.v1._errors import to_http_error
from app.database.session import get_db
from app.models.nursing_task import NursingTask, TaskStatus, TaskPriority, TaskType
from app.models.role import RoleName
from app.models.user import User
from app.repositories import nursing_task_repository
from app.schemas.nursing_task import NursingTaskCreate, NursingTaskUpdate
from app.schemas.response import success
from app.services.exceptions import NotFoundError, PermissionError_

router = APIRouter(prefix="/nursing-tasks", tags=["nursing-tasks"])


@router.get("")
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    patient_id: Optional[uuid.UUID] = Query(None, description="Filter by patient"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.NURSE, RoleName.DOCTOR, RoleName.ADMIN)),
) -> dict:
    """List nursing tasks for the current user."""
    try:
        # Convert status string to enum by value (e.g., "pending" -> TaskStatus.PENDING)
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status.lower())
            except ValueError:
                # Try matching by name for backward compatibility
                status_enum = TaskStatus[status.upper()] if hasattr(TaskStatus, status.upper()) else None
        
        tasks = nursing_task_repository.list_for_nurse(
            db, current_user.id, status=status_enum
        )
        
        return success(data=[
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "task_type": t.task_type.value,
                "status": t.status.value,
                "priority": t.priority.value,
                "patient_id": str(t.patient_id),
                "patient_name": f"{t.patient.first_name} {t.patient.last_name}",
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ])
    except Exception as e:
        raise to_http_error(e) from e


@router.post("")
def create_task(
    request: NursingTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.NURSE, RoleName.DOCTOR, RoleName.ADMIN)),
) -> dict:
    """Create a new nursing task."""
    try:
        task = NursingTask(
            patient_id=request.patient_id,
            title=request.title,
            description=request.description,
            task_type=request.task_type.value,
            priority=request.priority.value,
            assigned_to=request.assigned_to or current_user.id,
            assigned_by=current_user.id,
            due_date=request.due_date,
        )
        nursing_task_repository.add(db, task)
        db.commit()
        
        return success(
            data={
                "id": str(task.id),
                "title": task.title,
                "status": task.status.value,
            },
            message="Task created successfully"
        )
    except Exception as e:
        raise to_http_error(e) from e


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: uuid.UUID,
    request: NursingTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.NURSE, RoleName.DOCTOR, RoleName.ADMIN)),
) -> dict:
    """Update task status."""
    try:
        task = nursing_task_repository.get_by_id(db, task_id)
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        
        # Check permission - only assignee or admin can update
        if task.assigned_to != current_user.id and current_user.role.name != RoleName.ADMIN:
            raise PermissionError_("You can only update your own tasks")
        
        # Convert schema enum to model enum
        task.status = TaskStatus(request.status.value)
        if task.status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        nursing_task_repository.update(db, task)
        db.commit()
        
        return success(
            data={"id": str(task.id), "status": task.status.value},
            message="Task status updated"
        )
    except Exception as e:
        raise to_http_error(e) from e


@router.get("/stats")
def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleName.NURSE, RoleName.DOCTOR, RoleName.ADMIN)),
) -> dict:
    """Get task statistics for the current nurse."""
    try:
        pending_count = nursing_task_repository.count_pending_for_nurse(db, current_user.id)
        vitals_count = nursing_task_repository.count_vitals_due_for_nurse(db, current_user.id)
        
        # Get recent pending tasks
        recent_tasks = nursing_task_repository.list_pending_for_nurse(db, current_user.id, limit=5)
        
        return success(data={
            "pending_count": pending_count,
            "vitals_due_count": vitals_count,
            "recent_tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "patient_name": f"{t.patient.first_name} {t.patient.last_name}",
                    "task_type": t.task_type.value,
                    "priority": t.priority.value,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in recent_tasks
            ]
        })
    except Exception as e:
        raise to_http_error(e) from e
