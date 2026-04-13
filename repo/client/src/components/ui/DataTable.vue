<template>
  <div class="card">
    <div class="row toolbar">
      <input class="search" :value="search" placeholder="Search..." @input="onInput" />
      <button class="sort" aria-label="Toggle columns" @click="showColumns = !showColumns">Columns</button>
      <div v-if="showColumns" class="columns card">
        <label v-for="h in headers" :key="h" class="row">
          <input type="checkbox" :checked="visible[h] !== false" @change="toggleColumn(h)" />
          <small>{{ h }}</small>
        </label>
      </div>
      <slot name="filters" />
    </div>
    <table tabindex="0" @keydown.down.prevent="moveFocus(1)" @keydown.up.prevent="moveFocus(-1)">
      <thead>
        <tr>
          <th v-for="h in shownHeaders" :key="h">
            <button class="sort" @click="onSort(h)">{{ h }}</button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading"><td :colspan="shownHeaders.length"><BaseSkeleton /></td></tr>
        <tr v-else-if="rows.length === 0"><td :colspan="shownHeaders.length" class="muted">No records found.</td></tr>
        <tr v-else v-for="(row, idx) in rows" :key="idx" :class="{ active: focusIndex === idx }">
          <td v-for="h in shownHeaders" :key="h">{{ row[h] }}</td>
        </tr>
      </tbody>
    </table>
    <div class="row pager">
      <button class="sort" :disabled="page <= 1" @click="onPage(page - 1)">Prev</button>
      <small>Page {{ page }}</small>
      <button class="sort" :disabled="rows.length < pageSize" @click="onPage(page + 1)">Next</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSkeleton from "./BaseSkeleton.vue";
const props = defineProps<{ headers: string[]; rows: Record<string, unknown>[]; page: number; pageSize: number; search: string; loading?: boolean; storageKey?: string }>();
const emit = defineEmits<{ sort: [column: string]; page: [page: number]; "update:search": [value: string] }>();
const showColumns = ref(false);
const focusIndex = ref(0);
const visible = ref<Record<string, boolean>>({});
const persistedKey = computed(() => `table:${props.storageKey ?? props.headers.join(",")}`);
const shownHeaders = computed(() => props.headers.filter((h) => visible.value[h] !== false));

const persisted = localStorage.getItem(persistedKey.value);
if (persisted) {
  try {
    const parsed = JSON.parse(persisted) as { visible?: Record<string, boolean>; search?: string; page?: number };
    visible.value = parsed.visible ?? {};
    if (parsed.search) emit("update:search", parsed.search);
    if (parsed.page) emit("page", parsed.page);
  } catch {
    visible.value = {};
  }
}

watch(
  [visible, () => props.search, () => props.page],
  ([v, s, p]) => localStorage.setItem(persistedKey.value, JSON.stringify({ visible: v, search: s, page: p })),
  { deep: true }
);

function onInput(event: Event) {
  emit("update:search", (event.target as HTMLInputElement).value);
}

function onSort(header: string) {
  const raw = localStorage.getItem(persistedKey.value);
  const current = raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
  localStorage.setItem(persistedKey.value, JSON.stringify({ ...current, sort: header }));
  emit("sort", header);
}

function onPage(nextPage: number) {
  emit("page", nextPage);
}

function toggleColumn(header: string) {
  visible.value[header] = !(visible.value[header] !== false);
}

function moveFocus(delta: number) {
  if (props.rows.length === 0) return;
  const next = focusIndex.value + delta;
  focusIndex.value = Math.max(0, Math.min(props.rows.length - 1, next));
}
</script>

<style scoped>
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
.toolbar { justify-content: space-between; margin-bottom: 8px; }
.pager { justify-content: flex-end; margin-top: 8px; }
.search { border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px; }
.sort { border: 1px solid var(--border); border-radius: 6px; background: #fff; padding: 4px 8px; cursor: pointer; }
.columns {
  position: absolute;
  right: 12px;
  top: 42px;
  z-index: 5;
  min-width: 140px;
}
tbody tr:hover { background: #f8fafc; }
.active { background: #eff6ff; }
</style>
