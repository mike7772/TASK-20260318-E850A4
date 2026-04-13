<template>
  <header class="header row">
    <div class="row">
      <button v-if="!isAuthPage" class="toggle" aria-label="Toggle sidebar" @click="ui.toggleSidebar">☰</button>
      <h2>Activity Audit Platform</h2>
    </div>
    <small class="muted">{{ role }}</small>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useUiStore } from "@/app/store/uiStore";
defineProps<{ role: string }>();
const ui = useUiStore();
const route = useRoute();
const isAuthPage = computed(() => ["/login", "/register"].includes(route.path));
</script>

<style scoped>
.header {
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
h2 { font-size: 16px; margin: 0; }
.toggle {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: var(--radius);
  width: 32px;
  height: 32px;
  cursor: pointer;
  transition: transform .15s ease;
}
.toggle:hover { transform: scale(1.03); }
</style>
