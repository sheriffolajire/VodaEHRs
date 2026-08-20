"""Appointment scheduling business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.logger import AuditEvent, record_event
from app.models.appointment import Appointment
from app.models.role import RoleName
from app.models.user import User
from app.repositories import appointment_repository
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services import authorization
from app.services.audit_service import AuditService, AuditPriority
from app.services.exceptions import ConflictError, NotFoundError


def create_appointment(
    db: Session, 
    actor: User, 
    payload: AppointmentCreate,
    is_admin_override: bool = False
) -> Appointment:
    """Schedule an appointment, rejecting an exact double-booking.
    
    Layer 3: Resource Access (ensure_patient_access)
    Layer 4: Consent (ensure_consent) - Appointments require 'appointment' consent
    """
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, payload.patient_id)
    
    # Layer 4: Consent Check
    # Only check consent for clinicians (not admin/receptionist creating the appointment)
    if actor.role.name in (RoleName.DOCTOR, RoleName.NURSE):
        authorization.ensure_consent(
            db, actor, payload.patient_id,
            authorization.ResourceType.APPOINTMENT,
            is_admin_override
        )

    if appointment_repository.find_conflict(db, payload.clinician_id, payload.scheduled_at):
        raise ConflictError("The clinician already has an appointment at that time.")

    appointment = appointment_repository.add(
        db,
        Appointment(
            patient_id=payload.patient_id,
            clinician_id=payload.clinician_id,
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            reason=payload.reason,
            created_by=actor.id,
        ),
    )
    
    # Layer 5: Audit Logging
    AuditService.persist_audit_entry(
        db=db,
        action="appointment.create",
        user_id=actor.id,
        patient_id=payload.patient_id,
        status="success",
        reason=f"Created appointment: {appointment.reason or 'No reason provided'}",
        priority=AuditPriority.MEDIUM
    )
    db.commit()
    
    return appointment


def list_appointments(
    db: Session, 
    actor: User, 
    patient_id: uuid.UUID,
    is_admin_override: bool = False
) -> list[Appointment]:
    """List a patient's appointments after verifying access and consent.
    
    Layer 3: Resource Access (ensure_patient_access)
    Layer 4: Consent (ensure_consent) - Appointments require 'appointment' consent
    """
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, patient_id)
    
    # Layer 4: Consent Check
    # Patients can always see their own appointments
    # Admins and Receptionists can see all appointments
    # Clinicians need consent or must be the assigned clinician
    if actor.role.name in (RoleName.DOCTOR, RoleName.NURSE):
        try:
            authorization.ensure_consent(
                db, actor, patient_id,
                authorization.ResourceType.APPOINTMENT,
                is_admin_override
            )
        except Exception:
            # If no consent, only show appointments where they are the clinician
            all_appointments = appointment_repository.list_for_patient(db, patient_id)
            return [a for a in all_appointments if a.clinician_id == actor.id]
    
    return appointment_repository.list_for_patient(db, patient_id)


def update_appointment(
    db: Session, 
    actor: User, 
    appointment_id: uuid.UUID, 
    payload: AppointmentUpdate,
    is_admin_override: bool = False
) -> Appointment:
    """Reschedule, cancel, or complete an appointment.
    
    Layer 3: Resource Access (ensure_patient_access)
    Layer 4: Consent (ensure_consent) - Appointments require 'appointment' consent
    """
    appointment = appointment_repository.get_by_id(db, appointment_id)
    if appointment is None:
        raise NotFoundError("Appointment not found.")
    
    # Layer 3: Resource Access
    authorization.ensure_patient_access(db, actor, appointment.patient_id)
    
    # Layer 4: Consent Check
    # Creator (scheduled by) can always update
    # Assigned clinician can always update
    # Others need consent
    if appointment.created_by != actor.id and appointment.clinician_id != actor.id:
        if actor.role.name in (RoleName.DOCTOR, RoleName.NURSE):
            authorization.ensure_consent(
                db, actor, appointment.patient_id,
                authorization.ResourceType.APPOINTMENT,
                is_admin_override
            )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    db.flush()

    # Layer 5: Audit Logging
    AuditService.persist_audit_entry(
        db=db,
        action="appointment.update",
        user_id=actor.id,
        patient_id=appointment.patient_id,
        status="success",
        reason=f"Updated appointment: {appointment.reason or 'No reason provided'}",
        priority=AuditPriority.MEDIUM
    )
    db.commit()
    
    return appointment
