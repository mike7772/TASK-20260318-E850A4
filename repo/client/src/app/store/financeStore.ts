import { defineStore } from "pinia";
import * as financeService from "@/services/financeService";
import { useUiStore } from "@/app/store/uiStore";

export const useFinanceStore = defineStore("finance", {
  state: () => ({
    transactions: [] as Array<{ id: number; amount: number; type: string }>,
    loading: false,
    budgetUsage: 0,
    total: 0
  }),
  actions: {
    async fetchTransactions() {
      const ui = useUiStore();
      this.loading = true;
      try {
        const res = await financeService.listTransactions();
        this.transactions = res.items;
        this.total = res.total;
      } catch (err) {
        ui.handleError(err);
      } finally {
        this.loading = false;
      }
    },
    async setBudget(applicationId: number, amount: number) {
      const ui = useUiStore();
      try {
        return await financeService.setBudget(applicationId, amount);
      } catch (err) {
        ui.handleError(err);
        throw err;
      }
    },
    async addExpense(applicationId: number, amount: number, confirm = false) {
      const ui = useUiStore();
      try {
        return await financeService.addTransaction(applicationId, amount, confirm);
      } catch (err) {
        ui.handleError(err);
        throw err;
      }
    }
  }
});
