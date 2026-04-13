import { test, expect, type APIRequestContext, type Page } from "@playwright/test";
import { adminLogin, provisionUser, registerApplicant } from "./utils/bootstrap";

async function loginAs(page: Page, username: string) {
  await page.goto("/login");
  await page.getByTestId("username").fill(username);
  await page.getByTestId("password").fill("password");
  await page.getByTestId("login-button").click();
  await expect(page.getByTestId("login-message")).toHaveText("Login success");
}

test("register login upload review history flow", async ({ page, request }) => {
  const applicantName = `app_${Date.now()}`;
  const reviewerName = `rev_${Date.now()}`;
  const admin = await adminLogin(request);
  await registerApplicant(request, applicantName);
  await provisionUser(request, admin.accessToken, reviewerName, "reviewer");

  await loginAs(page, applicantName);
  await page.goto("/applications");
  await page.getByText("Next").click();
  await page.getByText("Next").click();
  await page.getByTestId("create-app").click();

  const apps = await request.get("/api/v1/applications");
  const appId = (await apps.json()).items[0].id as number;

  const uploadResp = await request.post("/api/v1/files/upload", {
    headers: { "Idempotency-Key": `pw-upload-${Date.now()}` },
    multipart: {
      application_id: String(appId),
      material_type: "1",
      file: {
        name: "doc.pdf",
        mimeType: "application/pdf",
        buffer: Buffer.from("%PDF-1.4")
      }
    }
  });
  expect(uploadResp.ok()).toBeTruthy();

  await page.goto("/login");
  await loginAs(page, reviewerName);
  await page.goto("/workflow");
  await page.getByPlaceholder("Application ID").fill(String(appId));
  await page.getByPlaceholder("Version").fill("1");
  await page.getByTestId("review-apply").click();
  await page.getByText("Submit").click();
  await expect(page.getByTestId("review-state")).toHaveText("Approved");

  await page.getByTestId("view-history").click();
  await expect(page.getByTestId("history-list")).toContainText("Submitted -> Approved");
});
