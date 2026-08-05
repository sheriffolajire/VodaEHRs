/** Audit log service for Phase 5.
 *
 * View and verify tamper-evident audit logs.
 */
import { apiClient } from "./apiClient";
import type { SuccessResponse } from "@/types/api";

export interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  clinician_id: string | null;
  clinician_name: string | null;
  patient_id: string | null;
  patient_name: string | null;
  status: string;
  reason: string | null;
  ip_address: string | null;
  priority: string;
  hash: string;
  prev_hash: string;
}

export interface ChainStatus {
  chain_ok: boolean;
  broken_at_index: number | null;
  total_entries: number;
  last_entry_time: string | null;
  last_entry_hash: string | null;
}

export interface VerifyResult {
  is_valid: boolean;
  total_entries: number;
  broken_at: number | null;
  message: string;
}

export interface AuditFilters {
  patient_id?: string;
  clinician_id?: string;
  action?: string;
  priority?: string;
  limit?: number;
  offset?: number;
}

export const auditService = {
  /** List audit logs with optional filtering. */
  async listAuditLogs(filters: AuditFilters = {}): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    if (filters.patient_id) params.append("patient_id", filters.patient_id);
    if (filters.clinician_id) params.append("clinician_id", filters.clinician_id);
    if (filters.action) params.append("action", filters.action);
    if (filters.priority) params.append("priority", filters.priority);
    if (filters.limit) params.append("limit", filters.limit.toString());
    if (filters.offset) params.append("offset", filters.offset.toString());

    const { data } = await apiClient.get<SuccessResponse<AuditLog[]>>(`/audit/logs?${params.toString()}`);
    return data.data;
  },

  /** Get a specific audit log entry. */
  async getAuditLog(logId: string): Promise<AuditLog> {
    const { data } = await apiClient.get<SuccessResponse<AuditLog>>(`/audit/logs/${logId}`);
    return data.data;
  },

  /** Get the status of the audit hash chain. */
  async getChainStatus(): Promise<ChainStatus> {
    const { data } = await apiClient.get<SuccessResponse<ChainStatus>>("/audit/chain-status");
    return data.data;
  },

  /** Verify the integrity of the entire audit hash chain. */
  async verifyChain(): Promise<VerifyResult> {
    const { data } = await apiClient.post<SuccessResponse<VerifyResult>>("/audit/verify");
    return data.data;
  },

  /** Verify a single audit log entry's hash. */
  async verifyEntry(logId: string): Promise<{ log_id: string; is_valid: boolean }> {
    const { data } = await apiClient.get<SuccessResponse<{ log_id: string; is_valid: boolean }>>(`/audit/logs/${logId}/verify`);
    return data.data;
  },

  /** List all unique action types. */
  async listActions(): Promise<string[]> {
    const { data } = await apiClient.get<SuccessResponse<string[]>>("/audit/actions");
    return data.data;
  },

  /** List high priority audit logs. */
  async listHighPriority(limit: number = 100, offset: number = 0): Promise<AuditLog[]> {
    const { data } = await apiClient.get<SuccessResponse<AuditLog[]>>(`/audit/high-priority?limit=${limit}&offset=${offset}`);
    return data.data;
  },
};
