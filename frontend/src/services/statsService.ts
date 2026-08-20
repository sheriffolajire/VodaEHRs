/**
 * Stats service for Phase 6 dashboards.
 * 
 * Provides role-based statistics for dashboard displays.
 */

import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";

export interface AdminStats {
  users_by_role: Record<string, number>;
  patient_count: number;
  record_count: number;
  appointments_by_status: Record<string, number>;
  recent_audit_events: Array<{
    id: string;
    action: string;
    user_id: string | null;
    status: string;
    created_at: string;
  }>;
}

export interface DoctorStats {
  assigned_patients: number;
  upcoming_appointments: Array<{
    id: string;
    patient_id: string;
    patient_name: string;
    scheduled_at: string;
    reason: string | null;
  }>;
  recent_records: Array<{
    id: string;
    patient_id: string;
    record_type: string;
    created_at: string;
    created_by: string;
  }>;
  active_emergency_access: boolean;
}

export interface PatientStats {
  record_count_by_type: Record<string, number>;
  upcoming_appointments: number;
  active_consents: number;
  document_count: number;
}

export interface AuditorStats {
  events_by_action: Record<string, number>;
  break_glass_count: number;
  chain_ok: boolean;
  total_entries: number;
  last_entry_time: string | null;
}

export interface SystemStats {
  db_status: "ok" | "error";
  minio_status: "ok" | "error";
  recent_errors: Array<{
    id: string;
    action: string;
    reason: string;
    created_at: string;
  }>;
  counts: {
    users: number;
    patients: number;
    records: number;
    appointments: number;
    documents: number;
  };
  // Extended fields for monitoring
  database?: {
    connected: boolean;
    latency_ms: number;
    active_connections: number;
    uptime_hours?: number;
  };
  storage?: {
    healthy: boolean;
    used_bytes: number;
    total_bytes: number;
    buckets?: number;
  };
  uptime_hours?: number;
}

/**
 * Get admin dashboard statistics.
 */
export async function getAdminStats(): Promise<AdminStats> {
  const { data } = await apiClient.get<SuccessResponse<AdminStats>>("/stats/admin");
  return data.data;
}

/**
 * Get doctor/nurse dashboard statistics.
 */
export async function getDoctorStats(): Promise<DoctorStats> {
  const { data } = await apiClient.get<SuccessResponse<DoctorStats>>("/stats/doctor");
  return data.data;
}

/**
 * Get patient dashboard statistics.
 */
export async function getPatientStats(): Promise<PatientStats> {
  const { data } = await apiClient.get<SuccessResponse<PatientStats>>("/stats/patient");
  return data.data;
}

/**
 * Get auditor dashboard statistics.
 */
export async function getAuditorStats(): Promise<AuditorStats> {
  const { data } = await apiClient.get<SuccessResponse<AuditorStats>>("/stats/auditor");
  return data.data;
}

/**
 * Get system monitoring statistics.
 */
export async function getSystemStats(): Promise<SystemStats> {
  const { data } = await apiClient.get<SuccessResponse<SystemStats>>("/stats/system");
  return data.data;
}
