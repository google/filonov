<template>
  <div class="time-series-chart">
    <div class="row items-center q-mb-md">
      <q-select
        v-model="selectedNodes"
        :options="availableNodes"
        multiple
        use-chips
        :label="`Add nodes`"
        class="col-grow"
        emit-value
        option-label="label"
      >
        <template v-slot:selected-item="scope">
          <q-chip
            removable
            @remove="scope.removeAtIndex(scope.index)"
            :tabindex="scope.tabindex"
            >{{ scope.opt.name }}</q-chip
          >
        </template>
      </q-select>
    </div>
    <apexchart
      type="line"
      :options="chartOptions"
      :series="series"
      :height="height"
    />
    <div class="row q-gutter-md q-mt-lg">
      <NodeCard
        v-for="node in selectedNodes"
        :key="node.id"
        :node="getNode(node.id)"
        @remove="removeNode(node.id)"
        style="width: 300px"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useQuasar } from 'quasar';
import { ApexOptions } from 'apexcharts';
import { ComputedRef } from 'vue';
import { Node } from 'components/models';
import NodeCard from './NodeCard.vue';

interface SelectOption {
  label: string;
  id: number;
  metric: number;
}

interface Props {
  data: Array<{ date: Date; value: number }>;
  metric: string;
  height?: number;
  clusterNodes: Node[];
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
});

const $q = useQuasar();
const selectedNodes = ref<SelectOption[]>([]);

const availableNodes = computed(() =>
  props.clusterNodes
    .map((node: Node) => ({
      id: node.id,
      label: `${node.label} (${node.name}, ${props.metric}: ${node.info![props.metric]})`,
      name: node.label,
      // series: node.series,
      metric: node.info![props.metric] as number,
    }))
    .sort((a, b) => b.metric - a.metric),
);

const series = computed(() => {
  // Start with cluster average series
  const allSeries = [
    {
      name: 'Cluster',
      data: props.data.map((d) => ({
        x: d.date.getTime(),
        y: d.value,
      })),
    },
  ];

  // Add selected nodes series
  selectedNodes.value.forEach((opt) => {
    const node = props.clusterNodes.find((n) => n.id === opt.id);
    if (node?.series) {
      allSeries.push({
        name: `Node ${node.id}`,
        data: Object.entries(node.series)
          .map(([date, metrics]) => ({
            x: new Date(date).getTime(),
            y: metrics[props.metric] as number,
          }))
          .sort((a, b) => a.x - b.x),
      });
    }
  });

  return allSeries;
});

const chartOptions: ComputedRef<ApexOptions> = computed(() => ({
  chart: {
    type: 'line',
  },
  xaxis: {
    type: 'datetime',
    labels: {
      style: {
        colors: $q.dark.isActive ? '#FFFFFF' : '#333333',
      },
    },
  },
  yaxis: {
    title: {
      text: props.metric,
      style: {
        color: $q.dark.isActive ? '#FFFFFF' : '#333333',
      },
    },
    labels: {
      formatter: (val) => val.toFixed(2),
      style: {
        colors: $q.dark.isActive ? '#FFFFFF' : '#333333',
      },
    },
  },
  tooltip: {
    shared: true,
    intersect: false,
    theme: $q.dark.isActive ? 'dark' : 'light',
    x: {
      format: 'yyyy-MM-dd',
    },
  },
  stroke: {
    curve: 'smooth',
    width: 2,
  },
  markers: {
    size: 4,
    hover: {
      size: 6,
    },
  },
}));

function getNode(nodeId: number) {
  return props.clusterNodes.find((node) => node.id === nodeId)!;
}

function removeNode(nodeId: number) {
  selectedNodes.value = selectedNodes.value.filter(
    (node) => node.id !== nodeId,
  );
}
</script>

<style scoped>
.time-series-chart {
  width: 100%;
}
</style>
