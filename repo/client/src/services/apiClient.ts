type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export class ApiError extends Error {
  status: number;
  correlationId: string | null;
  detail: unknown;
  constructor(status: number, detail: unknown, correlationId: string | null) {
    super(`Request failed (${status})`);
    this.status = status;
    this.detail = detail;
    this.correlationId = correlationId;
  }
}

const cache = new Map<string, { at: number; data: unknown }>();
const TTL_MS = 8000;

async function fetchJson(path: string, method: HttpMethod, body?: unknown, headers?: Record<string, string>) {
  const started = performance.now();
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const mergedHeaders: Record<string, string> = {
    ...(sessionStorage.getItem("accessToken") ? { Authorization: `Bearer ${sessionStorage.getItem("accessToken")}` } : {}),
    ...(headers ?? {})
  };
  if (!isFormData) {
    mergedHeaders["Content-Type"] = mergedHeaders["Content-Type"] ?? "application/json";
  } else {
    delete mergedHeaders["Content-Type"];
  }
  const res = await fetch(path, {
    method,
    headers: mergedHeaders,
    body: body ? (isFormData ? (body as FormData) : JSON.stringify(body)) : undefined
  });
  const elapsed = Math.round(performance.now() - started);
  const correlationId = res.headers.get("X-Correlation-ID");
  console.info("[api]", method, path, "latency_ms=", elapsed, "correlation=", correlationId);
  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) {
    if (res.status === 401) {
      sessionStorage.removeItem("accessToken");
      window.location.href = "/login";
    }
    throw new ApiError(res.status, payload, correlationId);
  }
  return payload;
}

export async function apiRequest<T>(path: string, method: HttpMethod, body?: unknown, headers?: Record<string, string>): Promise<T> {
  const key = `${method}:${path}:${JSON.stringify(body ?? null)}`;
  if (method === "GET") {
    const cached = cache.get(key);
    if (cached) {
      if (Date.now() - cached.at >= TTL_MS) {
        void fetchJson(path, method, body, headers).then((fresh) => cache.set(key, { at: Date.now(), data: fresh })).catch(() => undefined);
      }
      return cached.data as T;
    }
  }
  const payload = await fetchJson(path, method, body, headers);
  if (method === "GET") cache.set(key, { at: Date.now(), data: payload });
  return payload as T;
}
