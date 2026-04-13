<template>
  <textarea class="field" v-bind="$attrs" />
</template>

<style scoped>
.field {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  min-height: 96px;
  background: #fff;
}
</style>
