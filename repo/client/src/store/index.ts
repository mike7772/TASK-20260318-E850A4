import { defineStore } from "pinia";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    role: "guest" as "guest" | "applicant" | "reviewer" | "financial_admin",
    loggedIn: false
  }),
  actions: {
    loginAs(role: "applicant" | "reviewer" | "financial_admin") {
      this.role = role;
      this.loggedIn = true;
    }
  }
});
