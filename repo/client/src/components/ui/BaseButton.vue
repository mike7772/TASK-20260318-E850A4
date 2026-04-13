<template>
  <button :class="['btn', `btn-${variant}`]" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
}>();
</script>

<style scoped>
.btn {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.btn-secondary {
  background: #fff;
  color: var(--text);
}
.btn-danger {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}
</style>
