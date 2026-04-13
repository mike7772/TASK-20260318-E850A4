<template>
  <section class="col">
    <h3>Finance</h3>
    <div class="card col">
      <BaseInput v-model.number="applicationId" type="number" placeholder="Application ID" />
      <BaseInput v-model.number="budget" type="number" placeholder="Budget" />
      <BaseInput v-model.number="expense" type="number" placeholder="Expense" data-testid="expense" />
      <BaseButton @click="saveBudget">Save Budget</BaseButton>
      <BaseButton data-testid="check-finance" @click="addExpenseFlow">Add Expense</BaseButton>
      <small data-testid="finance-warning">{{ warning }}</small>
      <small class="muted">Overspending ratio: {{ overspendRatio }}%</small>
    </div>
    <DataTable
      :headers="['id','type','amount']"
      :rows="rows"
      :page="1"
      :page-size="20"
      :search="search"
      :loading="store.loading"
      @sort="() => undefined"
      @page="() => undefined"
      @update:search="onSearch"
    />
    <BaseModal :open="showConfirm" @close="showConfirm = false">
      <h4>Overspending confirmation</h4>
      <p>Expense exceeds 110% of budget. Continue?</p>
      <div class="row">
        <BaseButton variant="danger" @click="confirmExpense">Confirm</BaseButton>
        <BaseButton variant="secondary" @click="showConfirm = false">Cancel</BaseButton>
      </div>
    </BaseModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import DataTable from "@/components/ui/DataTable.vue";
import { useFinanceStore } from "@/app/store/financeStore";

const store = useFinanceStore();
const applicationId = ref(1);
const budget = ref(1000);
const expense = ref(0);
const warning = ref("Within budget");
const showConfirm = ref(false);
const search = ref("");
const overspendRatio = computed(() => {
  if (!budget.value) return 0;
  return Math.round((expense.value / budget.value) * 100);
});

const rows = computed(() => store.transactions.map((x) => ({ id: x.id, type: x.type, amount: x.amount })));
onMounted(() => store.fetchTransactions());

async function saveBudget() {
  await store.setBudget(applicationId.value, budget.value);
}

async function addExpenseFlow() {
  const res = await store.addExpense(applicationId.value, expense.value, false);
  if (res.requires_confirmation) {
    warning.value = "Secondary confirmation required";
    showConfirm.value = true;
    return;
  }
  warning.value = "Expense recorded";
  await store.fetchTransactions();
}

async function confirmExpense() {
  await store.addExpense(applicationId.value, expense.value, true);
  showConfirm.value = false;
  warning.value = "Expense recorded";
  await store.fetchTransactions();
}

function onSearch(value: string) {
  search.value = value;
}
</script>
