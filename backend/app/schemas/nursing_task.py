"""Nursing task schemas."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskType(str, enum.Enum):
    """Task type options."""
    VITALS = "vitals"
    MEDICATION = "medication"
    WOUND_CARE = "wound_care"
    PATIENT_EDUCATION = "patient_education"
    ASSESSMENT = "assessment"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class TaskPriority(str, enum.Enum):
    """Task priority options."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    """Task status options."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NursingTaskCreate(BaseModel):
    """Schema for creating a nursing task."""
    patient_id: uuid.UUID = Field(..., description="Patient ID to assign task to")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    task_type: TaskType = Field(..., description="Type of nursing task")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority")
    description: Optional[str] = Field(None, description="Optional task description")
    due_date: Optional[datetime] = Field(None, description="Optional due date")
    assigned_to: Optional[uuid.UUID] = Field(None, description="Nurse to assign to (defaults to current user)")


class NursingTaskUpdate(BaseModel):
    """Schema for updating a nursing task status."""
    status: TaskStatus = Field(..., description="New task status")


class NursingTaskResponse(BaseModel):
    """Schema for nursing task response."""
    id: uuid.UUID
    title: str
    description: Optional[str]
    task_type: str
    status: str
    priority: str
    patient_id: uuid.UUID
    patient_name: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
