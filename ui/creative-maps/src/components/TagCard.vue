<template>
  <q-card class="tag-card q-mb-md">
    <q-card-section class="q-py-sm bg-primary text-white">
      <div class="row items-center no-wrap">
        <div class="col">
          <div class="text-subtitle1 text-weight-bold">{{ tagData.tag }}</div>
        </div>
        <div class="col-auto">
          <q-btn flat dense round icon="close" @click="$emit('remove')" />
        </div>
      </div>
    </q-card-section>

    <q-card-section>
      <div class="row q-col-gutter-sm">
        <div class="col-12">
          <div class="text-caption text-grey">Frequency</div>
          <div class="text-body1">{{ tagData.freq }}</div>
        </div>
        <div class="col-12">
          <div class="text-caption text-grey">Average Score</div>
          <div class="text-body1">{{ tagData.avgScore.toFixed(2) }}</div>
        </div>
        <div class="col-12">
          <div class="text-caption text-grey">Nodes</div>
          <div class="text-body1">{{ tagData.nodes.length }}</div>
        </div>
        <div
          v-if="selectedMetric && tagData.metrics[selectedMetric] !== undefined"
          class="col-12"
        >
          <div class="text-caption text-grey">
            {{ capitalize(selectedMetric) }}
          </div>
          <div class="text-body1">
            {{
              formatMetricValue(tagData.metrics[selectedMetric], selectedMetric)
            }}
          </div>
        </div>
      </div>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn
        flat
        color="primary"
        label="View Nodes"
        icon="visibility"
        @click="$emit('view-nodes')"
      />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { TagStatsWithMetrics } from './models';
import { formatMetricValue } from 'src/helpers/graph';
import { capitalize } from 'src/helpers/utils';

interface Props {
  tagData: TagStatsWithMetrics;
  selectedMetric?: string;
}

defineProps<Props>();

defineEmits<{
  (e: 'remove'): void;
  (e: 'view-nodes'): void;
}>();
</script>

<style scoped>
.tag-card {
  width: 250px;
  transition: all 0.2s ease-in-out;
}

.tag-card:hover {
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
</style>
