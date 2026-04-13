import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/app/store/authStore";

const LoginPage = () => import("@/features/auth/LoginPage.vue");
const RegisterPage = () => import("@/features/auth/RegisterPage.vue");
const ApplicationWizardPage = () => import("@/features/applications/ApplicationWizardPage.vue");
const FileUploadPage = () => import("@/features/files/FileUploadPage.vue");
const WorkflowPage = () => import("@/features/workflow/WorkflowPage.vue");
const FinancePage = () => import("@/features/finance/FinancePage.vue");

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginPage },
    { path: "/register", component: RegisterPage },
    { path: "/applications", component: ApplicationWizardPage, meta: { permission: "application:read" } },
    { path: "/files", component: FileUploadPage, meta: { permission: "file:upload" } },
    { path: "/workflow", component: WorkflowPage, meta: { permission: "workflow:transition" } },
    { path: "/finance", component: FinancePage, meta: { permission: "finance:transaction" } }
  ]
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  await auth.init();
  if (to.path === "/login" || to.path === "/register") {
    return true;
  }
  if (!auth.accessToken) {
    return "/login";
  }
  if (!auth.role || auth.role === "guest") {
    return "/login";
  }
  const permission = to.meta.permission as string | undefined;
  if (!permission || auth.can(permission)) {
    return true;
  }
  return "/login";
});
