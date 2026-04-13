<template>
  <section class="card col">
    <h3>Sign in</h3>
    <small class="muted">Username and password only.</small>
    <BaseInput v-model="username" placeholder="Username" aria-label="Username" data-testid="username" @keydown.enter="submit" />
    <BaseInput v-model="password" type="password" placeholder="Password" aria-label="Password" data-testid="password" @keydown.enter="submit" />
    <BaseButton data-testid="login-button" @click="submit">Login</BaseButton>
    <small data-testid="login-message">{{ message }}</small>
    <small class="muted">No account? <router-link to="/register">Register</router-link></small>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import { useAuthStore } from "@/app/store/authStore";
import { useUiStore } from "@/app/store/uiStore";

const auth = useAuthStore();
const ui = useUiStore();
const router = useRouter();
const username = ref("");
const password = ref("");
const message = ref("Not logged in");

async function submit() {
  try {
    await auth.login(username.value, password.value);
    message.value = "Login success";
    ui.pushToast("Authenticated", "success");
    await router.push("/applications");
  } catch {
    message.value = "Login failed";
    ui.pushToast("Authentication failed", "error");
  }
}
</script>
