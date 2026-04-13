<template>
  <AppShell>
    <p v-if="ui.inlineError" class="error">{{ ui.inlineError }}</p>
    <router-view />
    <ToastStack :items="ui.toasts" />
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "./components/layout/AppShell.vue";
import ToastStack from "./components/ui/ToastStack.vue";
import { useUiStore } from "./app/store/uiStore";

const ui = useUiStore();
</script>

<style scoped>
.error {
  margin: 12px 20px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #991b1b;
}
</style>
