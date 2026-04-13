<template><div class="skel" /></template>
<style scoped>
.skel {
  width: 100%;
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, #eceff3, #f7f8fa, #eceff3);
  background-size: 200% 100%;
  animation: pulse 1.2s linear infinite;
}
@keyframes pulse { to { background-position: -200% 0; } }
</style>
