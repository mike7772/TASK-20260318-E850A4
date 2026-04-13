<template>
  <div class="shell">
    <SidebarNav v-if="!isAuthPage" />
    <div class="content">
      <AppHeader :role="auth.role" />
      <main class="main"><slot /></main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import SidebarNav from "./SidebarNav.vue";
import AppHeader from "./AppHeader.vue";
import { useAuthStore } from "@/app/store/authStore";
const auth = useAuthStore();
const route = useRoute();
const isAuthPage = computed(() => ["/login", "/register"].includes(route.path));
</script>

<style scoped>
.shell { min-height: 100vh; display: flex; }
.content { flex: 1; }
.main { padding: 20px; }
</style>
