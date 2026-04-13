import { apiRequest } from "./apiClient";

export async function getDuplicateCheckStatus() {
  return apiRequest<{ enabled: boolean; note: string }>("/api/v1/system/duplicate-check", "GET");
}
