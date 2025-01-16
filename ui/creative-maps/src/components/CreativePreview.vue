<template>
  <q-card class="creative-dialog">
    <q-card-section class="row items-center">
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-card-section class="q-pa-none content-section">
      <template v-if="isVideo">
        <iframe
          :src="getEmbedUrl(media_path)"
          class="creative-preview video"
          allowfullscreen
        ></iframe>
      </template>
      <template v-else>
        <img :src="image" class="creative-preview image" />
      </template>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
//import { Node } from 'components/models';

interface Props {
  //node: Node;
  media_path: string;
  image: string;
}
const props = defineProps<Props>();

const isVideo = computed(() => {
  return props.media_path?.includes('youtube.com');
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
