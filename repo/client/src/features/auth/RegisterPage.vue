<template>
  <section class="card col">
    <h3>Create account</h3>
    <BaseInput v-model="username" placeholder="Username" aria-label="Username" @keydown.enter="submit" />
    <small v-if="errors.username" class="error">{{ errors.username }}</small>
    <BaseInput v-model="email" placeholder="Email (optional)" aria-label="Email" @keydown.enter="submit" />
    <BaseInput v-model="phoneNumber" placeholder="Phone (optional)" aria-label="Phone number" @keydown.enter="submit" />
    <BaseInput v-model="idNumber" placeholder="ID number (optional)" aria-label="ID number" @keydown.enter="submit" />
    <BaseInput v-model="password" type="password" placeholder="Password" aria-label="Password" @keydown.enter="submit" />
    <small v-if="errors.password" class="error">{{ errors.password }}</small>
    <BaseInput v-model="confirmPassword" type="password" placeholder="Confirm password" aria-label="Confirm password" @keydown.enter="submit" />
    <small v-if="errors.confirmPassword" class="error">{{ errors.confirmPassword }}</small>
    <BaseButton :disabled="submitting || !isValid" @click="submit">Register</BaseButton>
    <small class="muted">Already have an account? <router-link to="/login">Login</router-link></small>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import { register } from "@/services/authService";
import { useUiStore } from "@/app/store/uiStore";

const router = useRouter();
const ui = useUiStore();
const username = ref("");
const email = ref("");
const phoneNumber = ref("");
const idNumber = ref("");
const password = ref("");
const confirmPassword = ref("");
const submitting = ref(false);
const errors = reactive({ username: "", password: "", confirmPassword: "" });

const isValid = computed(() => username.value.trim() && password.value.trim() && confirmPassword.value.trim() && password.value === confirmPassword.value);

function validate() {
  errors.username = username.value.trim() ? "" : "Username is required";
  errors.password = password.value.trim() ? "" : "Password is required";
  errors.confirmPassword = confirmPassword.value.trim() ? "" : "Confirm password is required";
  if (!errors.confirmPassword && password.value !== confirmPassword.value) errors.confirmPassword = "Passwords do not match";
  return !errors.username && !errors.password && !errors.confirmPassword;
}

async function submit() {
  if (!validate()) return;
  submitting.value = true;
  try {
    await register({
      username: username.value,
      password: password.value,
      email: email.value.trim() || undefined,
      phone_number: phoneNumber.value.trim() || undefined,
      id_number: idNumber.value.trim() || undefined
    });
    ui.pushToast("Registration successful", "success");
    await router.push("/login");
  } catch (err) {
    ui.handleError(err);
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.error { color: var(--color-danger); font-size: 12px; margin-top: -4px; }
a { color: var(--color-primary); }
</style>
