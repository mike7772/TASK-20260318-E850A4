<template>
  <select class="field" v-bind="$attrs">
    <slot />
  </select>
</template>

<style scoped>
.field {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}
</style>
