<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab"
      class="tab"
      :class="{ active: modelValue === tab }"
      @click="$emit('update:modelValue', tab)"
    >
      {{ tab }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ tabs: string[]; modelValue: string }>();
defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<style scoped>
.tabs { display: flex; gap: 8px; }
.tab { border: 1px solid var(--border); background: #fff; padding: 6px 10px; border-radius: 8px; }
.active { border-color: var(--accent); color: var(--accent); }
</style>
