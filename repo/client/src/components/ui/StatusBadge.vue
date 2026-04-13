<template>
  <span :class="['badge', `badge-${tone}`]"><slot /></span>
</template>

<script setup lang="ts">
defineProps<{ tone?: "neutral" | "success" | "danger" | "warning" }>();
</script>

<style scoped>
.badge {
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  border: 1px solid transparent;
}
.badge-neutral { background: #f3f4f6; color: #374151; }
.badge-success { background: #dcfce7; color: #166534; }
.badge-danger { background: #fee2e2; color: #991b1b; }
.badge-warning { background: #fef3c7; color: #92400e; }
</style>
