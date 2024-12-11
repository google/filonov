<template>
  <q-card class="node-metrics-dialog">
    <q-card-section class="row items-center">
      <div class="text-h6">Node Metrics History</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-card-section>
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-grow">
          <q-select
            v-model="selectedMetric"
            :options="availableMetrics"
            label="Select metric"
            class="col-grow"
          />
        </div>
      </div>

      <apexchart
        v-if="selectedMetric"
        type="line"
        :options="chartOptions"
        :series="series"
        height="400"
      />
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { ApexOptions } from 'apexcharts';
import { Node } from 'components/models';

interface Props {
  node: Node;
}

const props = defineProps<Props>();
const selectedMetric = ref<string>('');

const availableMetrics = computed(() => {
  if (!props.node.info) return [];
  return Object.keys(props.node.info);
});

// Initialize with first available metric
if (availableMetrics.value.length > 0) {
  selectedMetric.value = availableMetrics.value[0];
}

const series = computed(() => {
  if (!selectedMetric.value || !props.node.series) return [];

  const data = Object.entries(props.node.series)
    .map(([date, metrics]) => ({
      x: new Date(date).getTime(),
      y: metrics[selectedMetric.value] as number,
    }))
    .sort((a, b) => a.x - b.x);

  return [
    {
      name: props.node.label,
      data,
    },
  ];
});

const chartOptions = computed<ApexOptions>(() => ({
  chart: {
    type: 'line',
    zoom: {
      enabled: true,
    },
  },
  markers: {
    size: 4,
    hover: {
      size: 6,
    },
  },
  stroke: {
    curve: 'smooth',
    width: 2,
  },
  tooltip: {
    x: {
      format: 'yyyy-MM-dd',
    },
    y: {
      formatter: (value: number) => value.toFixed(2),
    },
  },
  xaxis: {
    type: 'datetime',
    title: {
      text: 'Date',
    },
  },
  yaxis: {
    title: {
      text: selectedMetric.value,
    },
    labels: {
      formatter: (val: number) => val.toFixed(2),
    },
  },
}));
</script>

<style scoped>
.node-metrics-dialog {
  width: 900px;
  max-width: 90vw;
}
</style>
