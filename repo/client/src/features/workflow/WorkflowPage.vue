<template>
  <section class="col">
    <h3>Workflow Reviews</h3>
    <DataTable
      :headers="['id','status','version']"
      :rows="rows"
      :page="1"
      :page-size="20"
      :search="search"
      :loading="store.loading"
      @sort="onSort"
      @page="() => undefined"
      @update:search="onSearch"
    />
    <div class="card col">
      <BaseInput v-model.number="selectedId" type="number" placeholder="Application ID" />
      <BaseInput v-model.number="expectedVersion" type="number" placeholder="Version" />
      <BaseSelect v-model="nextState">
        <option v-for="action in actionOptions" :key="action">{{ action }}</option>
      </BaseSelect>
      <BaseButton data-testid="review-apply" @click="openConfirm">Apply Transition</BaseButton>
      <BaseButton data-testid="view-history" variant="secondary" @click="openHistory">View History</BaseButton>
      <small data-testid="review-state">{{ stateText }}</small>
    </div>
    <BaseModal :open="showReason" @close="showReason = false">
      <h4>Transition confirmation</h4>
      <BaseTextarea v-if="nextState === 'Rejected'" v-model="reason" placeholder="Rejection reason (required)" autofocus />
      <div class="row">
        <BaseButton @click="apply">Submit</BaseButton>
        <BaseButton variant="secondary" @click="showReason = false">Cancel</BaseButton>
      </div>
    </BaseModal>
    <BaseModal :open="showHistory" @close="showHistory = false">
      <h4>Application History</h4>
      <ul data-testid="history-list">
        <li v-for="row in store.history" :key="`${row.timestamp}-${row.to_state}`">
          {{ row.from_state }} -> {{ row.to_state }} | actor {{ row.actor }} | {{ row.timestamp }} | {{ row.reason || "n/a" }} | {{ row.correlation_id || "n/a" }}
        </li>
      </ul>
    </BaseModal>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import DataTable from "@/components/ui/DataTable.vue";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseSelect from "@/components/ui/BaseSelect.vue";
import BaseTextarea from "@/components/ui/BaseTextarea.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import { useWorkflowStore } from "@/app/store/workflowStore";

const store = useWorkflowStore();
const selectedId = ref(1);
const expectedVersion = ref(1);
const nextState = ref("Approved");
const reason = ref("");
const stateText = ref("Submitted");
const showReason = ref(false);
const showHistory = ref(false);
const search = ref("");

const rows = computed(() => store.reviews.map((x) => ({ id: x.id, status: x.status, version: x.version })));
const actionOptions = computed(() => {
  const current = store.reviews.find((x) => x.id === selectedId.value)?.status ?? "Submitted";
  if (["Approved", "Rejected", "Canceled"].includes(current)) return ["No valid transitions"];
  if (current === "Supplemented") return ["Approved", "Rejected"];
  return ["Approved", "Rejected", "Canceled", "Promoted from Waitlist", "Supplemented"];
});
onMounted(() => store.fetchReviews());

function openConfirm() {
  if (nextState.value === "No valid transitions") return;
  showReason.value = true;
}

async function apply() {
  const res = await store.transition(selectedId.value, nextState.value, expectedVersion.value, reason.value || undefined);
  stateText.value = res.status;
  showReason.value = false;
  await store.fetchReviews();
}

function onSort() {
  // Server-side sorting hook: backend review endpoint currently defaults by id.
}

function onSearch(value: string) {
  search.value = value;
}

async function openHistory() {
  await store.fetchHistory(selectedId.value);
  showHistory.value = true;
}
</script>
