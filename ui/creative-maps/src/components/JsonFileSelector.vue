<template>
  <div class="q-pa-md">
    <q-card class="q-mb-md">
      <q-card-section>
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

<script>
import { api } from 'boot/axios';

export default {
  name: 'JsonFileHandler',
  data() {
    return {
      sourceType: 'local',
      file: null,
      remoteUrl: '',
      error: null,
      loading: false,
    };
  },
  methods: {
    async handleFileUpload() {
      this.error = null;

      if (!this.file) return;

      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const jsonData = JSON.parse(e.target.result);
          this.processJsonData(jsonData, this.file.name);
        } catch (err) {
          this.error = 'Error parsing JSON file: ' + err.message;
        }
      };

      reader.onerror = () => {
        this.error = 'Error reading file';
      };

      reader.readAsText(this.file);
    },

    async handleRemoteFile() {
      const remoteUrl = this.removeUrl?.trim();
      if (!remoteUrl) return;

      this.error = null;
      this.loading = true;

      try {
        const response = await api.get(remoteUrl);
        this.processJsonData(response.data, remoteUrl);
      } catch (err) {
        this.error = 'Error fetching remote file: ' + err.message;
      } finally {
        this.loading = false;
      }
    },

    processJsonData(jsonData, source) {
      // Empty function for you to implement your own data handling
      console.log('Received JSON data:', jsonData);
      // You can emit the data to parent component if needed:
      this.$emit('json-loaded', { data: jsonData, origin: source });
    },
  },
};
</script>
