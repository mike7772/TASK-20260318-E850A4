<template>
  <div class="row">
    <div v-for="(step, idx) in steps" :key="step" class="row">
      <span :class="['dot', { active: idx <= current }]">{{ idx + 1 }}</span>
      <small>{{ step }}</small>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ steps: string[]; current: number }>();
</script>

<style scoped>
.dot {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #e5e7eb;
  display: inline-grid;
  place-items: center;
}
.active { background: var(--accent); color: #fff; }
</style>
