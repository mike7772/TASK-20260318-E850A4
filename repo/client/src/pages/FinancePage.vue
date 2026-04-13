<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "../store";

const budget = ref(1000);
const expense = ref(0);
const warning = ref("Within budget");
const auth = useAuthStore();
const roleWarning = ref("");

function check() {
  if (auth.role !== "financial_admin") {
    roleWarning.value = "Role restricted";
    return;
  }
  roleWarning.value = "";
  warning.value = expense.value > budget.value * 1.1 ? "Secondary confirmation required" : "Within budget";
}
</script>

<template>
  <section>
    <h2>Finance</h2>
    <label>
      Budget
      <input data-testid="budget" v-model.number="budget" type="number" />
    </label>
    <label>
      Expense
      <input data-testid="expense" v-model.number="expense" type="number" />
    </label>
    <button data-testid="check-finance" @click="check">Check</button>
    <p data-testid="finance-warning">{{ warning }}</p>
    <p data-testid="finance-role-warning">{{ roleWarning }}</p>
  </section>
</template>
