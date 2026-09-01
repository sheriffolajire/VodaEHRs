"""Nursing tasks model for tracking patient care activities.

Tasks can be assigned to nurses and tracked for completion.
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import created_at_column, uuid_pk

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User


class TaskStatus(str, enum.Enum):
    """Task status options."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, enum.Enum):
    """Types of nursing tasks."""
    VITALS = "vitals"
    MEDICATION = "medication"
    WOUND_CARE = "wound_care"
    PATIENT_EDUCATION = "patient_education"
    ASSESSMENT = "assessment"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class NursingTask(Base):
    """Nursing task for patient care tracking.
    
    Tasks can be assigned to nurses and tracked for completion.
    """
    __tablename__ = "nursing_tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    
    # Task details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[TaskType] = mapped_column(SQLEnum(TaskType, name="task_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status", values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.PENDING,
        nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority", values_callable=lambda x: [e.value for e in x]),
        default=TaskPriority.NORMAL,
        nullable=False
    )
    
    # Assignment
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), nullable=False)
    assigned_to: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Timing
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = created_at_column()
    
    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", lazy="joined")
    assignee: Mapped["User"] = relationship("User", foreign_keys=[assigned_to], lazy="joined")
    assigner: Mapped["User"] = relationship("User", foreign_keys=[assigned_by], lazy="joined")
    
    def __repr__(self) -> str:
        return f"<NursingTask {self.title} ({self.status.value})>"
