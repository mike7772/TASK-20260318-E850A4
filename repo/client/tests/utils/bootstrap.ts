import type { APIRequestContext } from "@playwright/test";

export type RoleName = "applicant" | "reviewer" | "financial_admin" | "system_admin";

export async function adminLogin(request: APIRequestContext) {
  const username = process.env.BOOTSTRAP_SYSTEM_ADMIN_USERNAME ?? "sysadmin";
  const password = process.env.BOOTSTRAP_SYSTEM_ADMIN_PASSWORD ?? "password";
  const res = await request.post("/api/v1/auth/login", { data: { username, password } });
  const body = await res.json();
  return { username, accessToken: body.access_token as string };
}

export async function provisionUser(request: APIRequestContext, adminAccessToken: string, username: string, role: Exclude<RoleName, "system_admin">) {
  await request.post("/api/v1/system/users", {
    data: { username, password: "password", role },
    headers: { Authorization: `Bearer ${adminAccessToken}` }
  });
  const login = await request.post("/api/v1/auth/login", { data: { username, password: "password" } });
  const body = await login.json();
  return { username, accessToken: body.access_token as string };
}

export async function registerApplicant(request: APIRequestContext, username: string) {
  await request.post("/api/v1/auth/register", { data: { username, password: "password" } });
  const login = await request.post("/api/v1/auth/login", { data: { username, password: "password" } });
  const body = await login.json();
  return { username, accessToken: body.access_token as string };
}

