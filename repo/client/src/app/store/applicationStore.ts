import { defineStore } from "pinia";
import * as applicationService from "@/services/applicationService";
import { useUiStore } from "@/app/store/uiStore";

export const useApplicationStore = defineStore("application", {
  state: () => ({
    items: [] as applicationService.Application[],
    loading: false,
    page: 1,
    size: 10,
    sortBy: "id",
    sortDir: "desc" as "asc" | "desc",
    search: "",
    total: 0
  }),
  actions: {
    async fetchAll() {
      const ui = useUiStore();
      this.loading = true;
      try {
        const res = await applicationService.listApplications({
          page: this.page,
          size: this.size,
          sortBy: this.sortBy,
          sortDir: this.sortDir
        });
        this.items = res.items;
        this.total = res.total;
      } catch (err) {
        ui.handleError(err);
      } finally {
        this.loading = false;
      }
    },
    async create(title: string, deadline: string) {
      await applicationService.createApplication(title, deadline);
      await this.fetchAll();
    }
  }
});
