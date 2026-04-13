<template>
  <section>
    <h2>Review Workflow</h2>
    <p data-testid="review-state">{{ state }}</p>
    <label>
      Batch Size
      <input data-testid="batch-size" v-model.number="batchSize" type="number" />
    </label>
    <button data-testid="batch-run" @click="runBatch">Run Batch</button>
    <p data-testid="batch-status">{{ batchStatus }}</p>
    <button data-testid="review-approve" @click="state = 'Approved'">Approve</button>
    <button data-testid="review-reject" @click="reject">Reject</button>
    <p data-testid="rejection-cycle">{{ cycle }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "../store";

const state = ref("Submitted");
const cycle = ref("Not rejected");
const batchSize = ref(1);
const batchStatus = ref("Idle");
const auth = useAuthStore();

function runBatch() {
  batchStatus.value = batchSize.value > 50 ? "Batch limit exceeded" : "Batch processed";
}

function reject() {
  if (auth.role !== "reviewer") {
    cycle.value = "Role restricted";
    return;
  }
  state.value = "Rejected";
  cycle.value = "Rejected then resubmitted";
  state.value = "Supplemented";
}
</script>
