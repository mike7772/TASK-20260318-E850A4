<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "../store";

const username = ref("");
const password = ref("");
const role = ref<"applicant" | "reviewer" | "financial_admin">("applicant");
const message = ref("Not logged in");
const auth = useAuthStore();

function submit() {
  if (username.value && password.value) {
    auth.loginAs(role.value);
    message.value = "Login success";
  } else {
    message.value = "Missing credentials";
  }
}
</script>

<template>
  <section>
    <h2>Login</h2>
    <form @submit.prevent="submit">
      <label>
        Username
        <input v-model="username" data-testid="username" />
      </label>
      <label>
        Password
        <input v-model="password" type="password" data-testid="password" />
      </label>
      <label>
        Role
        <select v-model="role" data-testid="role-select">
          <option value="applicant">applicant</option>
          <option value="reviewer">reviewer</option>
          <option value="financial_admin">financial_admin</option>
        </select>
      </label>
      <button data-testid="login-button" type="submit">Sign In</button>
    </form>
    <p data-testid="login-message">{{ message }}</p>
  </section>
</template>
