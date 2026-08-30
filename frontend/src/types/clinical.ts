/** Domain types for patients and clinical data, mirroring the backend. */

export type Gender = "male" | "female" | "other" | "unspecified";

export type RecordType =
  | "diagnosis"
  | "medication"
  | "nursing_note"
  | "lab_result"
  | "imaging"
  | "other";

export type AppointmentStatus = "scheduled" | "completed" | "cancelled";

export interface Signature {
  id: string;
  record_id: string;
  signer_id: string;
  signature: string;
  algorithm: string;
  created_at: string;
}

export interface EncryptedRecord {
  id: string;
  patient_id: string;
  record_type: RecordType;
  encrypted_data: string;
  nonce: string;
  auth_tag: string;
  hash: string;
  encrypted_aes_key: string;
  signatures: Signature[];
  created_by: string;
  created_at: string;
  version: number;
}

export type MedicalRecord = EncryptedRecord;

export interface Patient {
  id: string;
  hospital_number: string;
  first_name: string;
  last_name: string;
  dob: string;
  gender: Gender;
  email: string | null;
  phone: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  created_at: string;
}

export interface MedicalDocument {
  id: string;
  patient_id: string;
  record_id: string | null;
  filename: string;  // Server-generated readable filename (e.g., john-doe_lab-results_2025-01-15_abc12345.pdf)
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
  uploaded_by: string;
  encrypted: boolean;
  aes_key_hash: string | null;
  // Upload metadata
  upload_purpose?: "lab_results" | "prescriptions" | "imaging" | "consent_forms" | "general";
  uploaded_for?: string | null;
  uploaded_for_type?: "patient" | "department" | "external_provider" | "internal_reference" | null;
  // Consent requirement flag
  requires_consent?: boolean;
}

export interface Appointment {
  id: string;
  patient_id: string;
  clinician_id: string;
  scheduled_at: string;
  duration_minutes: number;
  status: AppointmentStatus;
  reason: string | null;
  created_at: string;
}

export interface PatientCreateInput {
  first_name: string;
  last_name: string;
  dob: string;
  gender: Gender;
  email?: string | null;
  phone?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
}
