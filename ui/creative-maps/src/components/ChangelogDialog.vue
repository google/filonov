<template>
  <q-dialog v-model="isOpen">
    <q-card
      style="
        width: 700px;
        max-width: 80vw;
        display: flex;
        flex-direction: column;
        max-height: 80vh;
      "
    >
      <q-card-section>
        <div class="text-h4">Changelog</div>
      </q-card-section>

      <q-card-section
        class="q-pt-none changelog-content"
        style="overflow-y: auto"
      >
        <div v-html="parsedChangelog"></div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Close" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { marked } from 'marked';

const isOpen = ref(false);
const changelogContent = ref('');

const parsedChangelog = computed(() => {
  return marked(changelogContent.value);
});

onMounted(async () => {
  try {
    const response = await fetch('/CHANGELOG.md');
    if (response.ok) {
      changelogContent.value = await response.text();
    } else {
      changelogContent.value = 'Could not load changelog.';
    }
  } catch (error) {
    console.error('Error fetching changelog:', error);
    changelogContent.value = 'Error loading changelog.';
  }
});

function open() {
  isOpen.value = true;
}

defineExpose({
  open,
});
</script>

<style scoped>
.changelog-content :deep(h3) {
  font-size: 1.25rem;
  font-weight: 500;
  line-height: 1.6;
  letter-spacing: 0.0075em;
  margin-top: 24px;
  margin-bottom: 16px;
}
</style>
