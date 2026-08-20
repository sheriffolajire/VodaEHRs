"""Idempotent seeding of roles, the initial admin account, .

Run after migrations:  python -m app.seed

This script seeds:
- Roles (Admin, Doctor, Nurse, Patient, Receptionist, Auditor)
- Initial admin account
- Sample clinicians with key pairs
- Sample patients
- Sample medical records with encryption
- Sample medical documents
"""

import os
import uuid
from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.crypto.hashing import hash_password
from app.crypto.keys import generate_clinician_key_pair
from app.database.session import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_document import MedicalDocument
from app.models.medical_record import MedicalRecord, RecordType
from app.models.patient import Gender, Patient
from app.models.patient_assignment import PatientAssignment
from app.models.role import Role, RoleName
from app.models.signature import Signature
from app.models.user import User, UserStatus
from app.models.user_keys import UserKey
from app.repositories import (
    appointment_repository,
    assignment_repository,
    document_repository,
    patient_repository,
    record_repository,
    role_repository,
    signatures_repository,
    user_keys_repository,
    user_repository,
)
from app.services.document_service import upload_document
from app.services.record_crypto_service import RecordCryptoService

logger = get_logger("application")

# Sample clinician users with realistic medical specialties
CLINICIAN_USERS = [
    {
        "email": "dr.smith@hospital.com",
        "password": "SecurePass123!",
        "first_name": "Sarah",
        "last_name": "Smith",
        "specialty": "Cardiology",
        "license_number": "CARD-2024-001"
    },
    {
        "email": "dr.johnson@hospital.com",
        "password": "SecurePass123!",
        "first_name": "Michael",
        "last_name": "Johnson",
        "specialty": "Pediatrics",
        "license_number": "PED-2024-002"
    },
    {
        "email": "dr.williams@hospital.com",
        "password": "SecurePass123!",
        "first_name": "Emma",
        "last_name": "Williams",
        "specialty": "Neurology",
        "license_number": "NEURO-2024-003"
    },
    {
        "email": "dr.brown@hospital.com",
        "password": "SecurePass123!",
        "first_name": "James",
        "last_name": "Brown",
        "specialty": "Surgery",
        "license_number": "SURG-2024-004"
    },
    {
        "email": "nurse.davis@hospital.com",
        "password": "SecurePass123!",
        "first_name": "Lisa",
        "last_name": "Davis",
        "specialty": "Critical Care",
        "license_number": "NURSE-2024-005"
    }
]

# Sample receptionist users
RECEPTIONIST_USERS = [
    {
        "email": "receptionist.johnson@hospital.com",
        "password": "SecurePass123!",
        "first_name": "Maria",
        "last_name": "Johnson",
        "department": "Front Desk",
        "employee_id": "REC-2024-001"
    },
    {
        "email": "receptionist.williams@hospital.com",
        "password": "SecurePass123!",
        "first_name": "David",
        "last_name": "Williams",
        "department": "Patient Services",
        "employee_id": "REC-2024-002"
    }
]

# Sample patients with realistic demographics
PATIENTS = [
    {
        "hospital_number": "VOD-2026-001",
        "first_name": "Robert",
        "last_name": "Wilson",
        "dob": date(1985, 3, 15),
        "gender": Gender.MALE,
        "email": "robert.wilson@email.com",
        "phone": "+1-555-0101",
        "emergency_contact_name": "Mary Wilson",
        "emergency_contact_phone": "+1-555-0102"
    },
    {
        "hospital_number": "VOD-2026-002",
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "dob": date(1992, 7, 22),
        "gender": Gender.FEMALE,
        "email": "jennifer.martinez@email.com",
        "phone": "+1-555-0103",
        "emergency_contact_name": "Carlos Martinez",
        "emergency_contact_phone": "+1-555-0104"
    },
    {
        "hospital_number": "VOD-2026-003",
        "first_name": "David",
        "last_name": "Anderson",
        "dob": date(1978, 11, 8),
        "gender": Gender.MALE,
        "email": "david.anderson@email.com",
        "phone": "+1-555-0105",
        "emergency_contact_name": "Lisa Anderson",
        "emergency_contact_phone": "+1-555-0106"
    }
]

# Sample medical records with realistic content
MEDICAL_RECORDS = [
    {
        "title": "Initial Cardiology Consultation",
        "record_type": RecordType.DIAGNOSIS,
        "content": """Patient presents with chest pain and shortness of breath. 
Blood pressure: 145/90 mmHg
Heart rate: 88 bpm
ECG shows sinus rhythm with no acute changes.
Recommended stress test and echocardiogram.
Prescribed lisinopril 10mg daily for hypertension management.""",
        "summary": "Cardiology consultation for hypertension and chest pain evaluation"
    },
    {
        "title": "Pediatric Routine Checkup",
        "record_type": RecordType.NURSING_NOTE,
        "content": """Healthy 6-year-old boy for routine checkup.
Weight: 22kg (50th percentile)
Height: 115cm (75th percentile)
Blood pressure: 95/60 mmHg
Heart and lungs clear.
Vision and hearing normal.
Up to date on vaccinations.
Dental hygiene excellent.""",
        "summary": "Routine pediatric wellness examination"
    },
    {
        "title": "Neurology Follow-up - Migraine Management",
        "record_type": RecordType.MEDICATION,
        "content": """Patient returns for migraine management follow-up.
Frequency reduced from daily to 2-3 times per week.
Currently taking propranolol 40mg twice daily.
Reports good tolerance, minimal side effects.
Sleep improved, quality of life better.
Continue current regimen, schedule 3-month follow-up.""",
        "summary": "Migraine treatment follow-up with positive response"
    }
]

# Sample appointments
APPOINTMENTS = [
    {
        "scheduled_time": datetime.now() + timedelta(days=3),
        "status": AppointmentStatus.SCHEDULED,
        "reason": "Follow-up consultation",
        "notes": "Patient requested early morning appointment"
    },
    {
        "scheduled_time": datetime.now() + timedelta(days=7),
        "status": AppointmentStatus.SCHEDULED,
        "reason": "Annual physical examination",
        "notes": "Routine health maintenance"
    }
]


def seed_users(db: Session, admin_user_id: uuid.UUID) -> List[User]:
    """Seed all users including clinicians and patients."""
    users = []
    
    # Get required roles
    doctor_role = role_repository.get_by_name(db, RoleName.DOCTOR)
    nurse_role = role_repository.get_by_name(db, RoleName.NURSE)
    patient_role = role_repository.get_by_name(db, RoleName.PATIENT)
    
    if not doctor_role or not nurse_role or not patient_role:
        logger.warning("Required roles not found, skipping user seeding")
        return users

    # Seed clinicians
    for clinician_data in CLINICIAN_USERS:
        # Check if user already exists
        existing_user = user_repository.get_by_email(db, clinician_data["email"])
        if existing_user:
            # Ensure the password matches the expected test password.
            # Overwrite the hash unconditionally to guarantee the login
            # credentials used by the test suite are valid, even if the
            # user was created in a previous test run with a different
            # password.
            existing_user.password_hash = hash_password(clinician_data["password"])
            db.add(existing_user)
            db.flush()
            users.append(existing_user)
            continue

        # Determine role (Doctors or Nurses)
        role = nurse_role if "nurse" in clinician_data["email"].lower() else doctor_role

        # Create user
        user = User(
            first_name=clinician_data["first_name"],
            last_name=clinician_data["last_name"],
            email=clinician_data["email"],
            password_hash=hash_password(clinician_data["password"]),
            role_id=role.id,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        db.flush()  # Get the user ID

        # Generate key pair for all clinicians (including nurses)
        try:
            public_pem, encrypted_private = generate_clinician_key_pair()

            # Store key pair
            user_key = UserKey(
                user_id=user.id,
                public_key=public_pem,
                encrypted_private_key=encrypted_private,
                algorithm="RSA-PSS-SHA256",
            )
            db.add(user_key)
            logger.info(
                f"Created key pair for clinician {clinician_data['first_name']} {clinician_data['last_name']}"
            )
        except Exception as e:
            logger.error(
                f"Failed to generate key pair for {clinician_data['email']}: {e}"
            )
            db.rollback()
            raise

        users.append(user)
        logger.info(
            f"Created clinician {clinician_data['first_name']} {clinician_data['last_name']}"
        )
    
    # Seed receptionist users
    receptionist_role = role_repository.get_by_name(db, RoleName.RECEPTIONIST)
    if receptionist_role:
        for receptionist_data in RECEPTIONIST_USERS:
            # Check if user already exists
            existing_user = user_repository.get_by_email(db, receptionist_data["email"])
            if existing_user:
                # Update password to ensure it matches expected test password
                existing_user.password_hash = hash_password(receptionist_data["password"])
                db.add(existing_user)
                db.flush()
                users.append(existing_user)
                logger.info(f"Updated receptionist {receptionist_data['email']}")
                continue
            
            # Create receptionist user
            user = User(
                first_name=receptionist_data["first_name"],
                last_name=receptionist_data["last_name"],
                email=receptionist_data["email"],
                password_hash=hash_password(receptionist_data["password"]),
                role_id=receptionist_role.id,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            db.flush()
            users.append(user)
            logger.info(
                f"Created receptionist {receptionist_data['first_name']} {receptionist_data['last_name']}"
            )
    else:
        logger.warning("Receptionist role not found, skipping receptionist seeding")
    
    # Seed patient users
    patient_user_mappings = {
        "robert.wilson@email.com": {
            "email": "robert.wilson@voda.com",
            "password": "patientpassword123"
        },
        "jennifer.martinez@email.com": {
            "email": "jennifer.martinez@voda.com", 
            "password": "patientpassword123"
        },
        "david.anderson@email.com": {
            "email": "david.anderson@voda.com",
            "password": "patientpassword123"
        }
    }
    
    for patient_data in PATIENTS:
        patient_email = patient_data["email"]
        if patient_email in patient_user_mappings:
            user_data = patient_user_mappings[patient_email]
            
            # Check if user already exists
            existing_user = user_repository.get_by_email(db, user_data["email"])
            if existing_user:
                users.append(existing_user)
                continue
            
            # Create patient user account
            user = User(
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                role_id=patient_role.id,
                status=UserStatus.ACTIVE
            )
            db.add(user)
            users.append(user)
            logger.info(f"Created patient user {user_data['email']}")
    
    db.flush()
    
    # Update patient records to match user emails
    for patient_data in PATIENTS:
        patient_email = patient_data["email"]
        if patient_email in patient_user_mappings:
            user_data = patient_user_mappings[patient_email]
            patient = patient_repository.get_by_email(db, patient_email)
            if patient:
                patient.email = user_data["email"]
                logger.info(f"Updated patient email from {patient_email} to {user_data['email']}")
    
    db.flush()
    return users


def seed_patients(db: Session, created_by_user_id: uuid.UUID) -> List[Patient]:
    """Seed sample patients."""
    patients = []
    
    for patient_data in PATIENTS:
        # Check if patient already exists
        existing_patient = patient_repository.get_by_hospital_number(db, patient_data["hospital_number"])
        if existing_patient:
            patients.append(existing_patient)
            continue
        
        # Create patient
        patient = Patient(
            hospital_number=patient_data["hospital_number"],
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            dob=patient_data["dob"],
            gender=patient_data["gender"],
            email=patient_data["email"],
            phone=patient_data["phone"],
            emergency_contact_name=patient_data["emergency_contact_name"],
            emergency_contact_phone=patient_data["emergency_contact_phone"],
            created_by=created_by_user_id
        )
        db.add(patient)
        patients.append(patient)
        logger.info(f"Created patient {patient_data['first_name']} {patient_data['last_name']}")
    
    db.flush()
    return patients


def seed_medical_records(db: Session, patients: List[Patient], clinicians: List[User]) -> List[MedicalRecord]:
    """Seed encrypted medical records.

    If a clinician is not available (e.g., clinicians list is empty), the
    record is attributed to the initial admin user to satisfy the non‑null
    ``created_by`` foreign‑key constraint.
    """
    records: List[MedicalRecord] = []

    # Initialize crypto service
    crypto_service = RecordCryptoService()

    # Resolve admin user once for fallback use
    admin_user = user_repository.get_by_email(db, settings.initial_admin_email)

    for i, record_data in enumerate(MEDICAL_RECORDS):
        if i >= len(patients):
            break

        patient = patients[i]
        clinician = clinicians[i % len(clinicians)] if clinicians else None

        # Determine the creator: clinician if present, otherwise admin.
        creator_id = clinician.id if clinician else admin_user.id if admin_user else None

        try:
            encrypted_record = crypto_service.encrypt_and_sign_record(
                db=db,
                patient_id=patient.id,
                content=record_data["content"],
                title=record_data["title"],
                record_type=record_data["record_type"],
                summary=record_data["summary"],
                created_by=creator_id,
            )
            records.append(encrypted_record)
            logger.info(f"Created encrypted medical record: {record_data['title']}")
        except Exception as e:
            logger.error(f"Failed to create encrypted record '{record_data['title']}': {e}")

    db.flush()
    return records


def seed_documents(db: Session, patients: List[Patient], clinicians: List[User]) -> List[MedicalDocument]:
    """Seed sample medical documents."""
    documents = []
    
    # Sample document data
    sample_documents = [
        ("Clinical Note", "text/plain", "Patient presented with mild symptoms. Vital signs stable. Recommended rest and follow-up in 3 days."),
        ("Lab Report", "application/pdf", "Complete blood count results within normal ranges. All vitals stable."),
        ("X-Ray Scan", "image/png", "Chest X-ray shows clear lungs with no abnormalities detected.")
    ]
    
    for i, (description, mime_type, content) in enumerate(sample_documents):
        if i >= len(patients):
            break
            
        patient = patients[i]
        clinician = clinicians[i % len(clinicians)] if clinicians else None
        
        # NOTE: Similar to record seeding, checking for existing documents via
        # ``list_for_patient`` can trigger lazy‑loading errors during the
        # initial seeding transaction. Since the test suite runs against a fresh
        # database each time, we can safely create documents unconditionally.
        # Duplicate seeding is harmless because the primary keys are generated
        # anew on each run.
        
        try:
            # Create document using service
            from io import BytesIO
            # Get admin user for fallback actor
            admin_user = user_repository.get_by_email(db, settings.initial_admin_email)
            
            filename = f"{description.lower().replace(' ', '_')}.txt"
            
            document = upload_document(
                db=db,
                actor=clinician if clinician else admin_user,
                patient_id=patient.id,
                filename=filename,
                content_type=mime_type,
                size_bytes=len(content.encode('utf-8')),
                data=BytesIO(content.encode('utf-8'))
            )
            documents.append(document)
            logger.info(f"Created encrypted document: {filename}")
        except Exception as e:
            logger.error(f"Failed to create document '{description}': {e}")
    
    db.flush()
    return documents


def seed_patient_assignments(db: Session, patients: List[Patient], clinicians: List[User], assigned_by_user_id: uuid.UUID) -> List[PatientAssignment]:
    """Seed patient-clinician assignments."""
    assignments = []
    
    # Assign each patient to a clinician
    for i, patient in enumerate(patients):
        clinician = clinicians[i % len(clinicians)]  # Round-robin assignment
        
        # Check if assignment already exists
        existing_assignment = assignment_repository.get_active(db, patient.id, clinician.id)
        if existing_assignment:
            assignments.append(existing_assignment)
            continue
        
        # Create assignment
        assignment = PatientAssignment(
            patient_id=patient.id,
            clinician_id=clinician.id,
            assigned_by=assigned_by_user_id
        )
        db.add(assignment)
        assignments.append(assignment)
        logger.info(f"Assigned patient {patient.first_name} {patient.last_name} to {clinician.first_name} {clinician.last_name}")
    
    db.flush()
    return assignments


def seed_appointments(db: Session, patients: List[Patient], clinicians: List[User]) -> List[Appointment]:
    """Seed sample appointments."""
    appointments = []
    
    for i, appt_data in enumerate(APPOINTMENTS):
        if i >= len(patients) or i >= len(clinicians):
            break
            
        patient = patients[i]
        clinician = clinicians[i]
        
        # Check if appointment already exists
        # Simple check - in practice you'd want more sophisticated duplicate detection
        existing_appts = appointment_repository.list_for_patient(db, patient.id)
        if existing_appts:
            appointments.extend(existing_appts)
            continue
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient.id,
            clinician_id=clinician.id,
            scheduled_at=appt_data["scheduled_time"],
            status=appt_data["status"],
            reason=appt_data["reason"],
            duration_minutes=30,
            created_by=clinician.id
        )
        db.add(appointment)
        appointments.append(appointment)
        logger.info(f"Created appointment for {patient.first_name} with Dr. {clinician.last_name}")
    
    db.flush()
    return appointments


def seed_roles(db: Session) -> None:
    """Insert any missing roles. Safe to run repeatedly."""
    for role_name in RoleName:
        if role_repository.get_by_name(db, role_name) is None:
            db.add(Role(name=role_name))
    db.flush()


def seed_admin(db: Session) -> None:
    """Create the initial admin account if it does not already exist."""
    if user_repository.get_by_email(db, settings.initial_admin_email) is not None:
        return

    admin_role = role_repository.get_by_name(db, RoleName.ADMIN)
    if admin_role is None:
        raise RuntimeError("Admin role missing; seed roles before the admin user.")

    db.add(
        User(
            first_name=settings.initial_admin_first_name,
            last_name=settings.initial_admin_last_name,
            email=settings.initial_admin_email,
            password_hash=hash_password(settings.initial_admin_password),
            role_id=admin_role.id,
        )
    )


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        # : Basic roles and admin
        seed_roles(db)
        seed_admin(db)
        db.commit()
        logger.info("Phase 1 & 2 complete: roles and initial admin ensured.")
        
        # Phase 3: Get admin user for created_by references
        admin_user = user_repository.get_by_email(db, settings.initial_admin_email)
        if not admin_user:
            raise RuntimeError("Admin user not found after seeding")
        
        # Enhanced data seeding
        users = seed_users(db, admin_user.id)
        patients = seed_patients(db, admin_user.id)
        # Commit the newly created users and patients so that their IDs are
        # guaranteed to exist before we create dependent records. This avoids
        # foreign‑key violations that can arise when the same session has been
        # rolled back earlier in the transaction.
        db.commit()
        # Refresh the admin user reference after the commit (its state may be
        # detached).
        admin_user = user_repository.get_by_email(db, settings.initial_admin_email)

        # Filter clinicians from users for other seeding functions
        clinicians = [u for u in users if u.role.name in (RoleName.DOCTOR, RoleName.NURSE)]
        assignments = seed_patient_assignments(db, patients, clinicians, admin_user.id)
        medical_records = seed_medical_records(db, patients, clinicians)
        documents = seed_documents(db, patients, clinicians)
        appointments = seed_appointments(db, patients, clinicians)
        
        db.commit()
        logger.info(f" complete: {len(users)} users, {len(patients)} patients, "
                   f"{len(assignments)} assignments, {len(medical_records)} records, "
                   f"{len(documents)} documents, {len(appointments)} appointments seeded.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
