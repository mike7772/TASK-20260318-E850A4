<template>
  <div class="stack">
    <div v-for="item in items" :key="item.id" class="toast" :class="item.type">{{ item.message }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ items: Array<{ id: string; message: string; type: "success" | "error" }> }>();
</script>

<style scoped>
.stack { position: fixed; right: 16px; bottom: 16px; display: grid; gap: 8px; z-index: 40; }
.toast { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; }
.success { border-left: 4px solid #16a34a; }
.error { border-left: 4px solid var(--danger); }
</style>
