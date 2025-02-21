<template>
  <div>
    <q-card class="q-mb-md">
      <q-card-section>
        <div class="row">
          <div class="q-gutter-sm col">
            <q-toggle
              v-model="optimizeGraph"
              label="Optimize graph"
              color="primary"
            />
          </div>
          <q-input
            v-model="threshold"
            dense
            clearable
            placeholder="Similarity threshold"
            class="col q-gutter-sm"
            @clear="threshold = ''"
          >
          </q-input>
        </div>
        <q-separator></q-separator>
        <q-space></q-space>
        <!-- Source Selection -->
        <div class="q-gutter-sm">
          <q-radio v-model="sourceType" val="local" label="Upload local file" />
          <q-radio
            v-model="sourceType"
            val="remote"
            label="Open a remote file"
          />
        </div>

        <!-- Local File Input -->
        <q-file
          v-if="sourceType === 'local'"
          v-model="file"
          class="q-mt-md"
          label="Choose JSON file"
          accept=".json"
          @update:model-value="handleFileUpload"
          outlined
        >
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <!-- Remote URL Input -->
        <q-input
          v-if="sourceType === 'remote'"
          v-model="remoteUrl"
          class="q-mt-md"
          label="Enter JSON file URL"
          outlined
          :loading="loading"
        >
          <template v-slot:append>
            <q-btn
              flat
              round
              icon="download"
              @click="handleRemoteFile"
              :disable="!remoteUrl"
            />
          </template>
        </q-input>

        <!-- Error message -->
        <q-banner v-if="error" class="bg-negative text-white q-mt-md">
          <template v-slot:avatar>
            <q-icon name="error" color="white" />
          </template>
          {{ error }}
          <template v-slot:action>
            <q-btn flat color="white" label="Dismiss" @click="error = null" />
          </template>
        </q-banner>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api } from 'boot/axios';

// Types
type SourceType = 'local' | 'remote';
interface JsonLoadedEvent {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  origin: string;
  optimizeGraph: boolean;
  threshold?: number;
}

// State
const sourceType = ref<SourceType>('local');
const file = ref<File | null>(null);
const remoteUrl = ref('');
const error = ref<string | null>(null);
const loading = ref(false);
const optimizeGraph = ref(true);
const threshold = ref('');

// Event emits
const emit = defineEmits<{
  (e: 'json-loaded', payload: JsonLoadedEvent): void;
}>();

// Methods
const handleFileUpload = async () => {
  error.value = null;
  if (!file.value) return;

  const reader = new FileReader();

  reader.onload = (e) => {
    try {
      const jsonData = JSON.parse(e.target?.result as string);
      processJsonData(jsonData, file.value!.name);
    } catch (err) {
      error.value = `Error parsing JSON file: ${(err as Error).message}`;
    }
  };

  reader.onerror = () => {
    error.value = 'Error reading file';
  };

  reader.readAsText(file.value);
};

const handleRemoteFile = async () => {
  const url = remoteUrl.value?.trim();
  if (!url) return;

  error.value = null;
  loading.value = true;

  try {
    const response = await api.get(url);
    processJsonData(response.data, url);
  } catch (err) {
    error.value = `Error fetching remote file: ${(err as Error).message}`;
  } finally {
    loading.value = false;
  }
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const processJsonData = (jsonData: any, source: string) => {
  console.log('Received JSON data:', jsonData);
  emit('json-loaded', {
    data: jsonData,
    origin: source,
    optimizeGraph: optimizeGraph.value,
    threshold: Number.isFinite(parseFloat(threshold.value))
      ? Number(threshold.value)
      : undefined,
  });
};
</script>
