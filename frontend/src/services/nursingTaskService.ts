/**
 * Nursing Task Service
 * 
 * Provides API integration for nursing tasks and care activities.
 */

import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";

export interface NursingTask {
  id: string;
  title: string;
  description: string | null;
  task_type: string;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  priority: "low" | "normal" | "high" | "urgent";
  patient_id: string;
  patient_name: string;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TaskStats {
  pending_count: number;
  vitals_due_count: number;
  recent_tasks: Array<{
    id: string;
    title: string;
    patient_name: string;
    task_type: string;
    priority: string;
    due_date: string | null;
  }>;
}

export interface CreateTaskRequest {
  patient_id: string;
  title: string;
  task_type: string;
  priority?: string;
  description?: string;
  due_date?: Date;
  assigned_to?: string;
}

/**
 * List nursing tasks for the current user.
 */
export async function listTasks(status?: string): Promise<NursingTask[]> {
  const params = status ? { status } : {};
  const response = await apiClient.get<SuccessResponse<NursingTask[]>>(
    "/nursing-tasks",
    { params }
  );
  return response.data.data;
}

/**
 * Get task statistics for the current nurse.
 */
export async function getTaskStats(): Promise<TaskStats> {
  const response = await apiClient.get<SuccessResponse<TaskStats>>(
    "/nursing-tasks/stats"
  );
  return response.data.data;
}

/**
 * Create a new nursing task.
 */
export async function createTask(request: CreateTaskRequest): Promise<{ id: string; title: string; status: string }> {
  const response = await apiClient.post<SuccessResponse<{ id: string; title: string; status: string }>>(
    "/nursing-tasks",
    request
  );
  return response.data.data;
}

/**
 * Update task status.
 */
export async function updateTaskStatus(
  taskId: string,
  status: string
): Promise<{ id: string; status: string }> {
  const response = await apiClient.patch<SuccessResponse<{ id: string; status: string }>>(
    `/nursing-tasks/${taskId}/status`,
    null,
    { params: { status } }
  );
  return response.data.data;
}

/**
 * Complete a task.
 */
export async function completeTask(taskId: string): Promise<void> {
  await updateTaskStatus(taskId, "completed");
}

/**
 * Start a task (mark as in_progress).
 */
export async function startTask(taskId: string): Promise<void> {
  await updateTaskStatus(taskId, "in_progress");
}
