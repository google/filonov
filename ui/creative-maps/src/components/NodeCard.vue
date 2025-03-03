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
      <div class="q-mt-sm" align="right">
        <q-btn
          v-if="showDrillDown"
          flat
          color="primary"
          @click="showMetrics = true"
          icon="show_chart"
          label="Show in dynamic"
        />
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
    <!-- Metrics Dialog -->
    <q-dialog v-model="showMetrics">
      <NodeMetricsDialog :node="node" />
    </q-dialog>
    <!-- Creative Dialog -->
    <q-dialog v-model="showCreative" maximized>
      <CreativePreview :image="node.image" :media_path="node.media_path" />
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Node } from 'components/models';
import { formatMetricValue } from 'src/helpers/graph';
import NodeMetricsDialog from './NodeMetricsDialog.vue';
import CreativePreview from './CreativePreview.vue';

interface Props {
  node: Node;
  noClose?: boolean;
  showDrillDown?: boolean;
}
defineProps<Props>();

defineEmits<{
  (e: 'remove'): void;
}>();

const showCreative = ref(false);
const showMetrics = ref(false);
</script>

<style scoped>
.node-preview {
  height: 200px;
  object-fit: contain;
}
</style>
