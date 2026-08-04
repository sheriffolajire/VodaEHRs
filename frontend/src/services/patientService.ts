import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser } from "@/types/auth";
import type { Patient, PatientCreateInput } from "@/types/clinical";

export async function listPatients(query?: string): Promise<Patient[]> {
  const { data } = await apiClient.get<SuccessResponse<Patient[]>>("/patients", {
    params: query ? { q: query } : undefined,
  });
  return data.data;
}

export async function getPatient(patientId: string): Promise<Patient> {
  const { data } = await apiClient.get<SuccessResponse<Patient>>(`/patients/${patientId}`);
  return data.data;
}

export async function registerPatient(input: PatientCreateInput): Promise<Patient> {
  const { data } = await apiClient.post<SuccessResponse<Patient>>("/patients", input);
  return data.data;
}

export async function updatePatient(
  patientId: string,
  input: Partial<Pick<Patient, "phone" | "emergency_contact_name" | "emergency_contact_phone">>,
): Promise<Patient> {
  const { data } = await apiClient.patch<SuccessResponse<Patient>>(
    `/patients/${patientId}`,
    input,
  );
  return data.data;
}

/** List active doctors and nurses (for assignment and scheduling). */
export async function listClinicians(): Promise<AuthUser[]> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser[]>>("/users/clinicians");
  return data.data;
}

export async function assignClinician(patientId: string, clinicianId: string): Promise<void> {
  await apiClient.post("/assignments", {
    patient_id: patientId,
    clinician_id: clinicianId,
  });
}
