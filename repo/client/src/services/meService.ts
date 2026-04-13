import { apiRequest } from "./apiClient";

export async function me() {
  return apiRequest<{ username: string; role: string; permissions: string[] }>("/api/v1/auth/me", "GET");
}

