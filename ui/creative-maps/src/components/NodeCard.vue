<template>
  <q-card>
    <q-img
      :src="node.image"
      class="node-preview"
      @click="showCreative = true"
      style="cursor: pointer"
    />

    <q-card-section>
      <div class="absolute-top-right">
        <q-btn
          v-if="!noClose"
          flat
          round
          dense
          icon="close"
          @click="$emit('remove')"
        />
      </div>
      <div class="text-h6">{{ node.label }}</div>
      <div class="text-caption">ID: {{ node.name }}</div>

      <div class="q-mt-sm">
        <div v-for="(value, key) in node.info" :key="key" class="q-mb-xs">
          <strong>{{ key }}:</strong> {{ formatMetricValue(value, key) }}
        </div>
      </div>

      <div class="q-mt-sm row q-gutter-xs">
        <q-chip
          v-for="tagInfo in node.tags"
          :key="tagInfo.tag"
          size="sm"
          outline
        >
          {{ tagInfo.tag }} ({{ tagInfo.score.toFixed(3) }})
        </q-chip>
      </div>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn
        v-if="node.media_path"
        flat
        color="primary"
        @click="showCreative = true"
        icon="open_in_new"
        label="View Creative"
      />
    </q-card-actions>
    <!-- Creative Dialog -->
    <q-dialog v-model="showCreative" maximized>
      <q-card class="creative-dialog">
        <q-card-section class="row items-center">
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pa-none content-section">
          <template v-if="isVideo">
            <iframe
              :src="getEmbedUrl(node.media_path)"
              class="creative-preview video"
              allowfullscreen
            ></iframe>
          </template>
          <template v-else>
            <img :src="node.image" class="creative-preview image" />
          </template>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Node } from 'components/models';
import { formatMetricValue } from 'src/helpers/utils';

interface Props {
  node: Node;
  noClose?: boolean;
}
const props = defineProps<Props>();

defineEmits<{
  (e: 'remove'): void;
}>();

const showCreative = ref(false);

const isVideo = computed(() => {
  return props.node.media_path?.includes('youtube.com');
});

const getEmbedUrl = (url: string) => {
  if (!url) return '';

  // Convert YouTube watch URLs to embed URLs
  if (url.includes('youtube.com/watch')) {
    const videoId = new URL(url).searchParams.get('v');
    return `https://www.youtube.com/embed/${videoId}`;
  }
  return url;
};

</script>

<style scoped>
.node-preview {
  height: 200px;
  object-fit: contain;
}
.content-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}
.creative-preview.video {
  width: 100%;
  height: 80vh; /* Set explicit height */
  max-width: 1280px; /* Optional: limit max width */
  border: none;
}
</style>
