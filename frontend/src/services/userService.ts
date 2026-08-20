import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser, Role, RoleName, UserStatus } from "@/types/auth";

export interface CreateUserInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: RoleName;
}

export async function listUsers(): Promise<AuthUser[]> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser[]>>("/users");
  return data.data;
}

export async function listClinicians(): Promise<AuthUser[]> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser[]>>("/users/clinicians");
  return data.data;
}

export async function listRoles(): Promise<Role[]> {
  const { data } = await apiClient.get<SuccessResponse<Role[]>>("/roles");
  return data.data;
}

export async function createUser(input: CreateUserInput): Promise<AuthUser> {
  const { data } = await apiClient.post<SuccessResponse<AuthUser>>("/users", input);
  return data.data;
}

export async function setUserStatus(userId: string, status: UserStatus): Promise<AuthUser> {
  const { data } = await apiClient.patch<SuccessResponse<AuthUser>>(`/users/${userId}`, {
    status,
  });
  return data.data;
}

export interface UpdateUserInput {
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: RoleName;
}

export async function updateUser(userId: string, input: UpdateUserInput): Promise<AuthUser> {
  const { data } = await apiClient.patch<SuccessResponse<AuthUser>>(`/users/${userId}`, input);
  return data.data;
}

export async function deleteUser(userId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}`);
}

// Assignment management
export interface Assignment {
  id: string;
  patient_id: string;
  clinician_id: string;
  assigned_by: string;
  assigned_at: string;
  revoked_at?: string;
}

export async function listAssignments(): Promise<Assignment[]> {
  const { data } = await apiClient.get<SuccessResponse<Assignment[]>>("/assignments");
  return data.data;
}

export async function listAssignmentsForPatient(patientId: string): Promise<Assignment[]> {
  const { data } = await apiClient.get<SuccessResponse<Assignment[]>>(`/assignments/patient/${patientId}`);
  return data.data;
}

export async function listAssignmentsForClinician(clinicianId: string): Promise<Assignment[]> {
  const { data } = await apiClient.get<SuccessResponse<Assignment[]>>(`/assignments/clinician/${clinicianId}`);
  return data.data;
}

export async function createAssignment(patientId: string, clinicianId: string): Promise<Assignment> {
  const { data } = await apiClient.post<SuccessResponse<Assignment>>("/assignments", {
    patient_id: patientId,
    clinician_id: clinicianId,
  });
  return data.data;
}

export async function revokeAssignment(assignmentId: string): Promise<void> {
  await apiClient.delete(`/assignments/${assignmentId}`);
}
