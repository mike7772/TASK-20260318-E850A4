<template><div class="loader" aria-label="loading" /></template>
<style scoped>
.loader {
  width: 22px;
  height: 22px;
  border: 2px solid #cbd5e1;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
