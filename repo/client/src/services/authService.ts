import { apiRequest } from "./apiClient";

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/v1/auth/login", "POST", { username, password });
}

export async function refresh(refreshToken: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/api/v1/auth/refresh", "POST", { refresh_token: refreshToken });
}

export async function logout(token: string) {
  return apiRequest<{ status: string }>("/api/v1/auth/logout?token=" + encodeURIComponent(token), "POST");
}

export async function register(data: { username: string; password: string; id_number?: string; phone_number?: string; email?: string }) {
  return apiRequest<{ status?: string; message?: string }>("/api/v1/auth/register", "POST", data);
}
