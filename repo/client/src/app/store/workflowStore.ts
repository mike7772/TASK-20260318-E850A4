import { defineStore } from "pinia";
import * as workflowService from "@/services/workflowService";
import { useUiStore } from "@/app/store/uiStore";

export const useWorkflowStore = defineStore("workflow", {
  state: () => ({
    reviews: [] as Array<{ id: number; status: string; version: number }>,
    loading: false,
    total: 0,
    history: [] as Array<{ from_state: string; to_state: string; actor: number; timestamp: string; reason: string | null; correlation_id: string | null }>
  }),
  actions: {
    async fetchReviews() {
      const ui = useUiStore();
      this.loading = true;
      try {
        const res = await workflowService.listReviews();
        this.reviews = res.items;
        this.total = res.total;
      } catch (err) {
        ui.handleError(err);
      } finally {
        this.loading = false;
      }
    },
    async transition(applicationId: number, toState: string, expectedVersion: number, reason?: string) {
      const ui = useUiStore();
      try {
        return await workflowService.transitionApplication(applicationId, toState, expectedVersion, reason);
      } catch (err) {
        ui.handleError(err);
        throw err;
      }
    },
    async fetchHistory(applicationId: number) {
      const ui = useUiStore();
      try {
        const res = await workflowService.getHistory(applicationId);
        this.history = res.items;
      } catch (err) {
        ui.handleError(err);
      }
    }
  }
});
