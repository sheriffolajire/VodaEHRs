/** Emergency access (break-glass) service for Phase 5.
 *
 * Doctors can request emergency access to bypass consent in urgent situations.
 */
import { apiClient } from "./apiClient";
import type { SuccessResponse } from "@/types/api";

export interface EmergencyAccess {
  id: string;
  clinician_id: string;
  clinician_name: string | null;
  patient_id: string;
  patient_name: string | null;
  reason: string;
  status: "pending" | "approved" | "rejected";
  granted_at: string;
  expires_at: string;
  revoked_at: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_notes: string | null;
  is_active: boolean;
  remaining_minutes: number;
}

export interface EmergencyAccessRequest {
  patient_id: string;
  reason: string;
}

export interface EmergencyAccessCheck {
  has_access: boolean;
  remaining_minutes: number;
}

export const emergencyAccessService = {
  /** Request emergency access (break-glass) for a patient.
   * Only doctors can request emergency access.
   * Access is granted for 30 minutes.
   */
  async requestEmergencyAccess(request: EmergencyAccessRequest): Promise<EmergencyAccess> {
    const { data } = await apiClient.post<SuccessResponse<EmergencyAccess>>("/emergency-access", request);
    return data.data;
  },

  /** List all active emergency access grants (admin only). */
  async listEmergencyAccess(): Promise<EmergencyAccess[]> {
    const { data } = await apiClient.get<SuccessResponse<EmergencyAccess[]>>("/emergency-access");
    return data.data;
  },

  /** List emergency access requests made by the current doctor. */
  async myEmergencyAccess(): Promise<EmergencyAccess[]> {
    const { data } = await apiClient.get<SuccessResponse<EmergencyAccess[]>>("/emergency-access/my");
    return data.data;
  },

  /** Revoke an emergency access early (admin only). */
  async revokeEmergencyAccess(emergencyId: string): Promise<void> {
    await apiClient.delete(`/emergency-access/${emergencyId}`);
  },

  /** Approve an emergency access request (admin only). */
  async approveEmergencyAccess(emergencyId: string, notes?: string): Promise<EmergencyAccess> {
    const { data } = await apiClient.post<SuccessResponse<EmergencyAccess>>(
      `/emergency-access/${emergencyId}/approve`,
      null,
      { params: { notes } }
    );
    return data.data;
  },

  /** Reject an emergency access request (admin only). */
  async rejectEmergencyAccess(emergencyId: string, notes?: string): Promise<EmergencyAccess> {
    const { data } = await apiClient.post<SuccessResponse<EmergencyAccess>>(
      `/emergency-access/${emergencyId}/reject`,
      null,
      { params: { notes } }
    );
    return data.data;
  },

  /** Check if active emergency access exists for a patient. */
  async checkEmergencyAccess(patientId: string): Promise<EmergencyAccessCheck> {
    const { data } = await apiClient.get<SuccessResponse<EmergencyAccessCheck>>(`/emergency-access/check/${patientId}`);
    return data.data;
  },
};
