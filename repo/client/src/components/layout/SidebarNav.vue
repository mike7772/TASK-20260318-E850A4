<template>
  <aside class="sidebar" :class="{ collapsed: ui.isSidebarCollapsed }">
    <router-link to="/applications"><span class="icon">A</span><span v-if="!ui.isSidebarCollapsed">Applications</span></router-link>
    <router-link to="/files"><span class="icon">F</span><span v-if="!ui.isSidebarCollapsed">Files</span></router-link>
    <router-link to="/workflow"><span class="icon">W</span><span v-if="!ui.isSidebarCollapsed">Workflow</span></router-link>
    <router-link to="/finance"><span class="icon">$</span><span v-if="!ui.isSidebarCollapsed">Finance</span></router-link>
  </aside>
</template>

<script setup lang="ts">
import { useUiStore } from "@/app/store/uiStore";
const ui = useUiStore();
</script>

<style scoped>
.sidebar {
  width: 240px;
  border-right: 1px solid var(--border);
  padding: 16px;
  display: grid;
  gap: 10px;
  transition: width .2s ease;
}
.collapsed { width: 64px; padding-inline: 8px; }
.icon {
  width: 20px;
  display: inline-grid;
  place-items: center;
}
a {
  color: var(--muted);
  text-decoration: none;
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px;
  border-radius: 8px;
  transition: background-color .15s ease;
}
a:hover { background: #f3f4f6; }
.router-link-active { color: var(--accent); font-weight: 600; }
</style>
