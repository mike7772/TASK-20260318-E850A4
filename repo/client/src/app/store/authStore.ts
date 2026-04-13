import { defineStore } from "pinia";
import * as authService from "@/services/authService";
import { me as meRequest } from "@/services/meService";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    role: "guest",
    permissions: [] as string[],
    username: "",
    accessToken: sessionStorage.getItem("accessToken") ?? "",
    refreshToken: ""
    ready: false,
    readyPromise: null as Promise<void> | null
  }),
  actions: {
    async init() {
      if (this.ready) return;
      if (this.readyPromise) return this.readyPromise;
      this.readyPromise = (async () => {
      if (!this.accessToken) {
        this.ready = true;
        return;
      }
      try {
        const res = await meRequest();
        this.username = res.username;
        this.role = res.role;
        this.permissions = res.permissions ?? [];
        if (!this.role || this.role === "guest") {
          throw new Error("Missing role");
        }
      } catch {
        await this.logout();
        window.location.href = "/login";
      } finally {
        this.ready = true;
        this.readyPromise = null;
      }
      })();
      return this.readyPromise;
    },
    async login(username: string, password: string) {
      const res = await authService.login(username, password);
      this.username = username;
      this.accessToken = res.access_token;
      this.refreshToken = res.refresh_token;
      sessionStorage.setItem("accessToken", res.access_token);
      this.ready = false;
      this.readyPromise = null;
      await this.init();
    },
    can(permission: string) {
      return this.permissions.includes(permission) || this.permissions.includes("*");
    },
    async logout() {
      try {
        if (this.accessToken) {
          await authService.logout(this.accessToken);
        }
      } finally {
        this.accessToken = "";
        this.refreshToken = "";
        this.role = "guest";
        this.permissions = [];
        this.username = "";
        this.ready = true;
        this.readyPromise = null;
        sessionStorage.removeItem("accessToken");
      }
    }
  }
});
