import { apiRequest } from "./apiClient";
import { newIdempotencyKey } from "../utils/idempotency";

export async function transitionApplication(applicationId: number, toState: string, expectedVersion: number, reason?: string) {
  return apiRequest<{ status: string; version: number }>(
    `/api/v1/workflow/${applicationId}/transition`,
    "POST",
    { to_state: toState, expected_version: expectedVersion, reason },
    { "Idempotency-Key": newIdempotencyKey("workflow") }
  );
}

export async function listReviews() {
  return apiRequest<{ total: number; items: Array<{ id: number; status: string; version: number }> }>("/api/v1/workflow/reviews?page=1&size=20", "GET");
}

export async function getHistory(applicationId: number) {
  return apiRequest<{ application_id: number; items: Array<{ from_state: string; to_state: string; actor: number; timestamp: string; reason: string | null; correlation_id: string | null }> }>(
    `/api/v1/workflow/${applicationId}/history`,
    "GET"
  );
}
