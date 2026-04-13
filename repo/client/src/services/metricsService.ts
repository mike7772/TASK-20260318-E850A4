import { apiRequest } from "./apiClient";

export async function getLatestMetrics() {
  return apiRequest<{ approval_rate: number; correction_rate: number; overspending_rate: number }>("/api/v1/metrics/latest", "GET");
}
