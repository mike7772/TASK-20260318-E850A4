<template>
  <section>
    <h2>Upload Materials</h2>
    <input data-testid="file-input" type="file" @change="onFileChange" />
    <p data-testid="upload-status">{{ status }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";

const status = ref("No file selected");
const allowed = ["application/pdf", "image/jpeg", "image/png"];
const maxFile = 20 * 1024 * 1024;

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    status.value = "No file selected";
    return;
  }
  if (!allowed.includes(file.type)) {
    status.value = "Invalid file type";
    return;
  }
  if (file.size > maxFile) {
    status.value = "File exceeds 20MB";
    return;
  }
  status.value = "File accepted";
}
</script>
