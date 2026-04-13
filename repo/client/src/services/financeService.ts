import { apiRequest } from "./apiClient";
import { newIdempotencyKey } from "../utils/idempotency";

export async function setBudget(applicationId: number, totalBudget: number) {
  return apiRequest<{ status: string; version: number }>(
    "/api/v1/finance/budget",
    "POST",
    { application_id: applicationId, total_budget: totalBudget },
    { "Idempotency-Key": newIdempotencyKey("budget") }
  );
}

export async function addTransaction(applicationId: number, amount: number, confirm = false) {
  return apiRequest<{ requires_confirmation: boolean; warning?: string }>(
    "/api/v1/finance/transactions",
    "POST",
    { application_id: applicationId, type: "expense", amount, confirm_overspend: confirm },
    { "Idempotency-Key": newIdempotencyKey("txn") }
  );
}

export async function listTransactions() {
  return apiRequest<{ total: number; items: Array<{ id: number; amount: number; type: string }> }>("/api/v1/finance/transactions?page=1&size=20", "GET");
}
