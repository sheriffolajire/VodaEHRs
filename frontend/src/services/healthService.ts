import { apiClient } from "@/services/apiClient";
import type { HealthData, SuccessResponse } from "@/types/api";

export async function fetchHealth(): Promise<HealthData> {
  const { data } = await apiClient.get<SuccessResponse<HealthData>>("/health");
  return data.data;
}
