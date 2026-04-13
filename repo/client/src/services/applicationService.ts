import { apiRequest } from "./apiClient";
import { newIdempotencyKey } from "../utils/idempotency";

export interface Application {
  id: number;
  title: string;
  status: string;
  version: number;
}

export async function createApplication(title: string, deadline: string) {
  return apiRequest<{ id: number; status: string; version: number }>(
    "/api/v1/applications",
    "POST",
    { title, deadline },
    { "Idempotency-Key": newIdempotencyKey("application-create") }
  );
}

export async function getApplicationForm() {
  return apiRequest<{ fields: Array<{ key: string; label: string; required: boolean; field_type: string }> }>("/api/v1/forms/application", "GET");
}

export async function listApplications(params: {
  page: number;
  size: number;
  sortBy: string;
  sortDir: "asc" | "desc";
  status?: string;
  search?: string;
}) {
  const query = new URLSearchParams({
    page: String(params.page),
    size: String(params.size),
    sort_by: params.sortBy,
    sort_dir: params.sortDir
  });
  if (params.status) query.set("status", params.status);
  return apiRequest<{ total: number; items: Application[] }>(`/api/v1/applications?${query.toString()}`, "GET");
}
