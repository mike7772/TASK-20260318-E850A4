<template>
  <section class="col">
    <h3>Application Wizard</h3>
    <BaseStepper :steps="['Details', 'Schedule', 'Confirm']" :current="step" />
    <div class="card col">
      <template v-if="step === 0">
        <BaseInput v-model="title" placeholder="Title" />
        <BaseInput v-model="description" placeholder="Description (optional)" />
        <BaseInput v-model="category" placeholder="Category (optional)" />
        <BaseInput v-model.number="requestedAmount" type="number" placeholder="Requested amount (optional)" />
      </template>
      <BaseInput v-if="step === 1" v-model="deadline" type="datetime-local" />
      <p v-if="step === 2" class="muted">
        Title: {{ title }} | Deadline: {{ deadline }} | Category: {{ category }} | Requested: {{ requestedAmount || "n/a" }}
      </p>
      <div class="row">
        <BaseButton variant="secondary" :disabled="step === 0" @click="step--">Back</BaseButton>
        <BaseButton v-if="step < 2" @click="step++">Next</BaseButton>
        <BaseButton v-else data-testid="create-app" @click="create">Submit</BaseButton>
      </div>
    </div>
    <DataTable
      :headers="['id','title','status','version']"
      :rows="rows"
      :page="store.page"
      :page-size="store.size"
      :search="store.search"
      :loading="store.loading"
      @sort="(col) => { store.sortBy = col; store.fetchAll(); }"
      @page="(p) => { store.page = p; store.fetchAll(); }"
      @update:search="(v) => { store.search = v; store.fetchAll(); }"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import BaseStepper from "@/components/ui/BaseStepper.vue";
import DataTable from "@/components/ui/DataTable.vue";
import { useApplicationStore } from "@/app/store/applicationStore";
import { useUiStore } from "@/app/store/uiStore";
import { getApplicationForm } from "@/services/applicationService";

const step = ref(0);
const title = ref("");
const description = ref("");
const category = ref("");
const requestedAmount = ref<number | null>(null);
const deadline = ref("");
const store = useApplicationStore();
const ui = useUiStore();
const rows = computed(() => store.items.map((x) => ({ id: x.id, title: x.title, status: x.status, version: x.version })));

onMounted(async () => {
  await store.fetchAll();
  // Fetch form definition for parity; current UI renders a minimal compatible subset.
  try {
    await getApplicationForm();
  } catch {
    // non-fatal
  }
});

async function create() {
  await store.create(title.value, new Date(deadline.value).toISOString());
  ui.pushToast("Application submitted", "success");
}
</script>
