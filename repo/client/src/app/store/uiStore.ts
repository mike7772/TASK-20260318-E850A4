import { defineStore } from "pinia";
import { ApiError } from "@/services/apiClient";

export const useUiStore = defineStore("ui", {
  state: () => ({
    toasts: [] as Array<{ id: string; message: string; type: "success" | "error" }>,
    inlineError: "",
    isSidebarCollapsed: false
  }),
  actions: {
    pushToast(message: string, type: "success" | "error") {
      const id = crypto.randomUUID();
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter((x) => x.id !== id);
      }, 2600);
    },
    handleError(err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 403) this.inlineError = "Access denied";
        else if (err.status === 409) this.inlineError = "Conflict detected. Refresh and retry.";
        else this.inlineError = `Request failed (${err.status})`;
        this.pushToast(this.inlineError, "error");
        return;
      }
      this.inlineError = "Unexpected error";
      this.pushToast("Unexpected error", "error");
    },
    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed;
    }
  }
});
