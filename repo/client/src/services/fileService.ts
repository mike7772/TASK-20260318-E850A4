import { apiRequest } from "./apiClient";
import { newIdempotencyKey } from "../utils/idempotency";

export async function uploadMaterial(payload: {
  applicationId: number;
  materialType: string;
  file: File;
}) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("application_id", String(payload.applicationId));
  formData.append("material_type", payload.materialType);
  return apiRequest<{ status: string; version: number; sha256: string }>(
    "/api/v1/files/upload",
    "POST",
    formData,
    { "Content-Type": "multipart/form-data", "Idempotency-Key": newIdempotencyKey("file") }
  );
}
