<template>
  <div v-if="open" class="backdrop" @click.self="$emit('close')">
    <div class="modal card" role="dialog" aria-modal="true" tabindex="-1" @keydown.esc="$emit('close')">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ open: boolean }>();
defineEmits<{ close: [] }>();
</script>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  display: grid;
  place-items: center;
  animation: fade .16s ease;
}
.modal { width: min(480px, 92vw); animation: scale .16s ease; }
@keyframes fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes scale { from { transform: scale(0.97); opacity: .85; } to { transform: scale(1); opacity: 1; } }
</style>
