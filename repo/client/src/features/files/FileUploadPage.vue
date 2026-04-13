<template>
  <section class="col">
    <h3>File Upload</h3>
    <div class="card col">
      <BaseInput v-model.number="applicationId" type="number" placeholder="Application ID" />
      <BaseInput v-model="materialType" type="text" placeholder="Material Type" />
      <div class="drop" @dragover.prevent @drop.prevent="onDrop">
        <input data-testid="file-input" type="file" multiple aria-label="Upload files" @change="onFileInput" />
        <small>Drag & drop multiple PDF/JPG/PNG files or click to browse</small>
      </div>
      <small data-testid="upload-status">{{ status }}</small>
      <div v-for="item in queue" :key="item.id" class="queue-item">
        <div class="row between">
          <small>{{ item.file.name }}</small>
          <small>{{ item.state }}</small>
        </div>
        <div class="progress"><div class="bar" :style="{ width: item.progress + '%' }" /></div>
        <div class="row">
          <BaseButton :disabled="item.state==='uploading'" @click="uploadItem(item.id)">Upload</BaseButton>
          <BaseButton variant="secondary" :disabled="item.state!=='failed'" @click="retryItem(item.id)">Retry</BaseButton>
          <BaseButton variant="secondary" :disabled="item.state!=='uploading'" @click="cancelItem(item.id)">Cancel</BaseButton>
        </div>
      </div>
      <ul><li v-for="v in versions" :key="v.version">Version {{ v.version }} - {{ v.filename }}</li></ul>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import BaseInput from "@/components/ui/BaseInput.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import { uploadMaterial } from "@/services/fileService";
import { useUiStore } from "@/app/store/uiStore";

const applicationId = ref(1);
const materialType = ref("1");
const status = ref("No file selected");
const versions = ref<Array<{ version: number; filename: string }>>([]);
const ui = useUiStore();
const queue = ref<Array<{ id: string; file: File; state: "queued" | "uploading" | "uploaded" | "failed" | "canceled"; progress: number; timer?: number }>>([]);
const checklist = ref<Array<{ id: number; code: string; name: string }>>([]);

onMounted(async () => {
  try {
    const res = await fetch("/api/v1/checklists/items", {
      headers: sessionStorage.getItem("accessToken") ? { Authorization: `Bearer ${sessionStorage.getItem("accessToken")}` } : {}
    });
    if (res.ok) {
      checklist.value = (await res.json()).items ?? [];
    }
  } catch {
    // non-fatal for upload UI
  }
});

function validateFile(file: File) {
  if (!["application/pdf", "image/png", "image/jpeg"].includes(file.type)) return "Invalid file type";
  if (file.size > 20 * 1024 * 1024) return "File exceeds 20MB";
  return "";
}

function addFiles(files: File[]) {
  for (const file of files) {
    const error = validateFile(file);
    if (error) {
      status.value = error;
      continue;
    }
    queue.value.push({ id: crypto.randomUUID(), file, state: "queued", progress: 0 });
  }
  status.value = queue.value.length ? "Files queued" : status.value;
}

function onFileInput(event: Event) {
  addFiles(Array.from((event.target as HTMLInputElement).files ?? []));
}

function onDrop(event: DragEvent) {
  addFiles(Array.from(event.dataTransfer?.files ?? []));
}

async function uploadItem(id: string) {
  const item = queue.value.find((q) => q.id === id);
  if (!item) return;
  item.state = "uploading";
  item.progress = 6;
  item.timer = window.setInterval(() => {
    item.progress = Math.min(item.progress + 10, 92);
  }, 140);
  try {
    const res = await uploadMaterial({
      applicationId: applicationId.value,
      materialType: materialType.value,
      file: item.file
    });
    item.progress = 100;
    item.state = "uploaded";
    versions.value = [{ version: res.version, filename: item.file.name }, ...versions.value].slice(0, 3);
    status.value = "Uploaded";
  } catch (err) {
    item.state = "failed";
    status.value = String((err as Error).message).includes("409") ? "Duplicate detected" : "Upload failed";
    ui.handleError(err);
  } finally {
    if (item.timer) window.clearInterval(item.timer);
  }
}

function retryItem(id: string) {
  uploadItem(id);
}

function cancelItem(id: string) {
  const item = queue.value.find((q) => q.id === id);
  if (!item) return;
  item.state = "canceled";
  if (item.timer) window.clearInterval(item.timer);
  item.progress = 0;
}
</script>

<style scoped>
.drop { border: 1px dashed var(--border); border-radius: 8px; padding: 12px; display: grid; gap: 8px; }
.progress { width: 100%; height: 8px; background: #e5e7eb; border-radius: 999px; overflow: hidden; }
.bar { height: 100%; background: var(--accent); transition: width .15s ease; }
.queue-item { border: 1px solid var(--border); border-radius: 8px; padding: 10px; display: grid; gap: 8px; }
.between { justify-content: space-between; }
</style>
