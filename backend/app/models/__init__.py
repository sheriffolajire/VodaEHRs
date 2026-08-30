"""ORM models package.

Importing the models here ensures they are registered on the shared metadata so
Alembic autogenerate can detect them.
"""

from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog, AuditPriority
from app.models.consent import Consent, ConsentStatus
from app.models.emergency_access import EmergencyAccess
from app.models.medical_document import MedicalDocument
from app.models.medical_record import MedicalRecord, RecordType
from app.models.nursing_task import NursingTask, TaskStatus, TaskPriority, TaskType
from app.models.password_reset_token import PasswordResetToken
from app.models.patient import Gender, Patient
from app.models.patient_assignment import PatientAssignment
from app.models.record_version import RecordVersion
from app.models.refresh_token import RefreshToken
from app.models.role import Role, RoleName
from app.models.signature import Signature
from app.models.user import User, UserStatus
from app.models.user_keys import UserKey

__all__ = [
    "Appointment",
    "AppointmentStatus",
    "AuditLog",
    "AuditPriority",
    "Consent",
    "ConsentStatus",
    "EmergencyAccess",
    "Gender",
    "MedicalDocument",
    "MedicalRecord",
    "NursingTask",
    "PasswordResetToken",
    "Patient",
    "PatientAssignment",
    "RecordType",
    "RecordVersion",
    "RefreshToken",
    "Role",
    "RoleName",
    "TaskPriority",
    "TaskStatus",
    "TaskType",
    "User",
    "UserStatus",
    "UserKey",
    "Signature",
]
