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
          <q-radio
            v-model="sourceType"
            val="google_drive"
            label="Open from Google Drive"
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
          label="Enter JSON file URL (can be gs://bucket/path)"
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

        <q-btn
          @click="openDrivePicker"
          :disabled="!isReady"
          class="q-mt-md"
          v-if="sourceType === 'google_drive'"
        >
          Select File from Google Drive
        </q-btn>

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
    <!-- Loading overlay -->
    <q-inner-loading :showing="loading" color="primary">
      <q-spinner-dots size="40px" />
      <div class="q-mt-sm">Loading data...</div>
    </q-inner-loading>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from 'boot/axios';

// Type definitions
interface TokenClientConfig {
  client_id: string;
  scope: string;
  callback: (response: TokenResponse) => void;
}

interface TokenClient {
  requestAccessToken(options?: { prompt?: string }): void;
  callback: (response: TokenResponse) => void;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
  error?: string;
}

declare global {
  interface Window {
    google: {
      accounts: {
        oauth2: {
          initTokenClient(config: TokenClientConfig): TokenClient;
        };
      };
      picker: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        View: new (viewId: string) => any;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        DocsView: new (viewId: string) => any;
        ViewId: { DOCS: string; DOCUMENTS: string; FOLDERS: string };
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ViewGroup: new (viewId?: string) => any;
        Action: { PICKED: string };
        Feature: { NAV_HIDDEN: string };
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        PickerBuilder: new () => any;
      };
    };
    gapi: {
      load(api: string, callback: () => void): void;
    };
    tokenClient: TokenClient | null;
    onApiLoad: () => void;
    gisLoaded: () => void;
  }
}

interface PickerDocument {
  id: string;
  name: string;
  mimeType: string;
  url: string;
}

interface PickerResponse {
  action: string;
  docs: PickerDocument[];
}

// Types
type SourceType = 'local' | 'remote' | 'google_drive';
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

onMounted(async () => {
  const gapiScript = document.createElement('script');
  gapiScript.src = 'https://apis.google.com/js/api.js';
  gapiScript.async = true;
  gapiScript.defer = true;
  gapiScript.onload = window.onApiLoad;
  document.body.appendChild(gapiScript);

  const gisScript = document.createElement('script');
  gisScript.src = 'https://accounts.google.com/gsi/client';
  gisScript.async = true;
  gisScript.defer = true;
  gisScript.onload = window.gisLoaded;
  document.body.appendChild(gisScript);

  const urlParams = new URLSearchParams(window.location.search);
  const fileId = urlParams.get('open');

  if (fileId) {
    if (fileId.startsWith('https://drive.google.com/')) {
      // TODO: extract fileId from the url
    }

    // Wait for APIs to load first
    await new Promise<void>((resolve) => {
      const checkReady = () => {
        if (window.tokenClient && pickerInited.value) {
          resolve();
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    });

    await loadDriveFile(fileId);
    window.location.search = '';
  }
});

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string;
const API_KEY = import.meta.env.VITE_GOOGLE_API_KEY as string;
const SCOPE =
  'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/devstorage.read_only';
const pickerInited = ref(false);
const gisInited = ref(false);
const isReady = ref(false);

window.onApiLoad = () => {
  window.gapi.load('picker', () => {
    pickerInited.value = true;
    checkReady();
  });
};
window.gisLoaded = () => {
  window.tokenClient = window.google.accounts.oauth2.initTokenClient({
    client_id: CLIENT_ID,
    scope: SCOPE,
    callback: () => {},
  });
  gisInited.value = true;
  checkReady();
};

const checkReady = () => {
  isReady.value = pickerInited.value && gisInited.value;
};

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
    if (url.startsWith('gs://')) {
      // gs://bucket/path/file.json" => "bucket/path/file.json"
      const path = url.substring('gs://'.length);
      const data = await fetchGcsFile(path);
      processJsonData(data, url);
    } else {
      const response = await api.get(url);
      processJsonData(response.data, url);
    }
  } catch (err) {
    error.value = `Error fetching remote file: ${(err as Error).message}`;
  } finally {
    loading.value = false;
  }
};

async function fetchGcsFile(path: string) {
  // Wait until APIs are loaded
  while (!window.tokenClient) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  // Get token
  const tokenResponse = await new Promise<TokenResponse>((resolve) => {
    window.tokenClient!.callback = (resp: TokenResponse) => resolve(resp);
    window.tokenClient!.requestAccessToken({ prompt: 'consent' });
  });

  const response = await fetch('https://storage.googleapis.com/' + path, {
    headers: {
      Authorization: `Bearer ${tokenResponse.access_token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch from GCS: ${response.status}`);
  }

  return await response.json();
}

const loadDriveFile = async (fileId: string) => {
  try {
    loading.value = true;

    // Wait until APIs are loaded
    while (!window.tokenClient) {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    // Get token
    const tokenResponse = await new Promise<TokenResponse>((resolve) => {
      window.tokenClient!.callback = (resp: TokenResponse) => resolve(resp);
      window.tokenClient!.requestAccessToken({ prompt: 'consent' });
    });

    // Fetch file metadata first to get the name
    const metadataResponse = await fetch(
      `https://www.googleapis.com/drive/v3/files/${fileId}?fields=name`,
      {
        headers: {
          Authorization: `Bearer ${tokenResponse.access_token}`,
        },
      },
    );

    if (!metadataResponse.ok) {
      throw new Error(
        `Failed to fetch file metadata: ${metadataResponse.status}`,
      );
    }

    const metadata = await metadataResponse.json();
    const fileName = metadata.name;

    // Fetch file content
    const response = await fetch(
      `https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`,
      {
        headers: {
          Authorization: `Bearer ${tokenResponse.access_token}`,
        },
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const jsonContent = await response.json();
    processJsonData(jsonContent, fileName);
  } catch (e) {
    console.error('Error loading file:', e);
    error.value = 'Failed to open picker';
  } finally {
    loading.value = false;
  }
};

const openDrivePicker = async () => {
  try {
    // Get access token
    const tokenResponse = await new Promise<TokenResponse>((resolve) => {
      if (window.tokenClient) {
        window.tokenClient.callback = (resp: TokenResponse) => resolve(resp);
        window.tokenClient.requestAccessToken({ prompt: 'consent' });
      }
    });

    // Create and render Picker
    const viewFiles = new window.google.picker.View(
      window.google.picker.ViewId.DOCS,
    );
    viewFiles.setMimeTypes('application/json');
    viewFiles.setLabel('Files');
    const viewFolder = new window.google.picker.DocsView(
      window.google.picker.ViewId.DOCS,
    );
    viewFolder.setMimeTypes('application/json');
    viewFolder.setIncludeFolders(true);
    viewFolder.setLabel('Folders');
    const picker = new window.google.picker.PickerBuilder()
      .setAppId(CLIENT_ID)
      .setOAuthToken(tokenResponse.access_token)
      .addView(viewFiles)
      .addView(viewFolder)
      .setDeveloperKey(API_KEY)
      .setCallback(pickerCallback)
      .build();

    picker.setVisible(true);

    setTimeout(() => {
      const pickerFrame = document.querySelector('.picker.picker-dialog');
      if (pickerFrame) {
        const frameElement = pickerFrame as HTMLElement;
        frameElement.style.zIndex = '7000';
      }
    }, 100);
  } catch (e) {
    console.error('Error opening picker:', e);
    error.value = 'Failed to open picker';
  }
};

const pickerCallback = async (data: PickerResponse) => {
  if (data.action === window.google.picker.Action.PICKED) {
    loading.value = true;
    const file = data.docs[0];
    try {
      // Get a new token for the API request
      const tokenResponse = await new Promise<TokenResponse>((resolve) => {
        if (window.tokenClient) {
          window.tokenClient.callback = (resp: TokenResponse) => resolve(resp);
          window.tokenClient.requestAccessToken({ prompt: '' });
        }
      });

      const response = await fetch(
        `https://www.googleapis.com/drive/v3/files/${file.id}?alt=media`,
        {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const jsonContent = await response.json();
      console.log(file);
      processJsonData(jsonContent, file.url);
    } catch (e) {
      console.error('Error fetching file content:', e);
      error.value = 'Failed to fetch file content';
    } finally {
      loading.value = false;
    }
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
