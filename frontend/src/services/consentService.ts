/** Consent management service for Phase 5.
 *
 * Patients grant/revoke consent for clinicians to access their records.
 */
import { apiClient } from "./apiClient";
import type { SuccessResponse } from "@/types/api";

export interface Consent {
  id: string;
  patient_id: string;
  clinician_id: string;
  clinician_name: string | null;
  record_type: string;
  granted: boolean;
  created_at: string;
  revoked_at: string | null;
  expires_at: string | null;
  is_active: boolean;
}

export interface ConsentGrantRequest {
  clinician_id: string;
  record_type: string;
}

export const consentService = {
  /** List all consents for the current patient. */
  async listConsents(): Promise<Consent[]> {
    const { data } = await apiClient.get<SuccessResponse<Consent[]>>("/consent");
    return data.data;
  },

  /** List only active consents. */
  async listActiveConsents(): Promise<Consent[]> {
    const { data } = await apiClient.get<SuccessResponse<Consent[]>>("/consent/active");
    return data.data;
  },

  /** Grant consent to a clinician for a specific record type. */
  async grantConsent(request: ConsentGrantRequest): Promise<Consent> {
    const { data } = await apiClient.post<SuccessResponse<Consent>>("/consent", request);
    return data.data;
  },

  /** Revoke a consent by ID. */
  async revokeConsent(consentId: string): Promise<void> {
    await apiClient.delete(`/consent/${consentId}`);
  },
};
