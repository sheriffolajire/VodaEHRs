/** Audit log service for Phase 5.
 *
 * View and verify tamper-evident audit logs.
 */
import { apiClient } from "./apiClient";
import type { SuccessResponse } from "@/types/api";

/**
 * `normal` is retained for audit records created before the LOW/MEDIUM split.
 * It must remain displayable because audit priority is part of the stored hash.
 */
export type AuditPriority = "normal" | "low" | "medium" | "high";
export type AuditCategory = "auth" | "access" | "modify" | "consent" | "emergency" | "security" | "system";

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
  priority: AuditPriority;
  category: AuditCategory;
  hash: string;
  prev_hash: string;
}

export interface ChainStatus {
  chain_ok: boolean;
  broken_at_index: number | null;
  total_entries: number;
  last_entry_time: string | null;
  last_entry_hash: string | null;
  broken_entry?: {
    id: string;
    action: string;
    created_at: string;
    entry_hash: string;
    prev_hash: string | null;
  } | null;
  previous_entry?: {
    id: string;
    action: string;
    created_at: string;
    entry_hash: string;
  } | null;
  expected_prev_hash?: string | null;
  actual_prev_hash?: string | null;
}

export interface VerifyResult {
  is_valid: boolean;
  total_entries: number;
  broken_at: number | null;
  message: string;
}

export interface RepairResult {
  repaired: boolean;
  total_entries?: number;
  repaired_entries?: number;
  message?: string;
  reason?: string;
}

export interface AuditFilters {
  patient_id?: string;
  clinician_id?: string;
  action?: string;
  priority?: string;
  category?: string;
  limit?: number;
  offset?: number;
}

export interface CategoryInfo {
  value: AuditCategory;
  name: string;
}

export interface PriorityInfo {
  value: AuditPriority;
  name: string;
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

  /** Repair the audit hash chain. */
  async repairChain(): Promise<RepairResult> {
    const { data } = await apiClient.post<SuccessResponse<RepairResult>>("/audit/repair-chain");
    return data.data;
  },

  /** List all available categories. */
  async listCategories(): Promise<CategoryInfo[]> {
    const { data } = await apiClient.get<SuccessResponse<CategoryInfo[]>>("/audit/categories");
    return data.data;
  },

  /** List all available priorities. */
  async listPriorities(): Promise<PriorityInfo[]> {
    const { data } = await apiClient.get<SuccessResponse<PriorityInfo[]>>("/audit/priorities");
    return data.data;
  },
};
