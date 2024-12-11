//NodeComparison.vue
<template>
  <q-card>
    <q-card-section class="row items-center">
      <div class="text-h6">Nodes Comparison</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-card-section class="row items-center">
      <q-btn-toggle
        v-model="isDynamicView"
        :options="[
          { label: 'Static', value: false },
          { label: 'Time Series', value: true },
        ]"
        class="q-mr-md"
      />
    </q-card-section>

    <q-card-section>
      <template v-if="isDynamicView">
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-auto">
            <q-select
              style="min-width: 200px"
              v-model="selectedMetric"
              :options="metrics"
              label="Metric"
            />
          </div>
          <div class="col-grow">
            <q-select
              v-model="selectedNodeIds"
              :disable="!selectedMetric"
              :options="sortedNodeOptions"
              multiple
              use-chips
              label="Select nodes"
              option-label="label"
            >
              <template #option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.name }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    {{
                      formatMetricValue(scope.opt.metricValue, selectedMetric)
                    }}
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>
        </div>

        <apexchart
          type="line"
          :options="chartOptions"
          :series="chartSeries"
          height="400"
        />

        <div class="row q-gutter-md q-mt-lg">
          <NodeCard
            v-for="node in selectedNodes"
            :key="node.id"
            :node="node"
            @remove="removeNode(node.id)"
            @click="selectNode(node.id)"
            style="width: 300px"
          />
        </div>
      </template>

      <template v-else>
        <q-table
          :rows="nodesMetrics"
          :columns="nodesListColumns"
          row-key="id"
          :pagination="{ rowsPerPage: 0 }"
        >
          <template #body-cell-name="props">
            <q-td :props="props">
              <a
                href="#"
                class="text-primary"
                @click.prevent="selectNode(props.row.id)"
              >
                {{ props.value }}
              </a>
            </q-td>
          </template>
        </q-table>
      </template>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { QTableColumn } from 'quasar';
import type { ApexOptions } from 'apexcharts';
import NodeCard from './NodeCard.vue';
import { Node } from './models';
import { capitalize, formatMetricValue } from 'src/helpers/utils';
import { isNumber } from 'lodash';

interface Props {
  nodes: Node[];
}

interface NodeOption {
  id: number;
  label: string;
  name: string;
  metricValue: number;
}

interface NodeMetrics {
  id: number;
  name: string;
  assetId: string;
  [key: string]: number | string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'select-node', nodeId: number): void;
}>();

const isDynamicView = ref(false);
const selectedNodeIds = ref<NodeOption[]>([]);
const selectedMetric = ref('');

const metrics = computed((): string[] => {
  const metricSet = new Set<string>();
  props.nodes.forEach((node) => {
    if (node.info) {
      Object.keys(node.info).forEach((metric) => metricSet.add(metric));
    }
  });
  return Array.from(metricSet);
});

const nodesMetrics = computed((): NodeMetrics[] => {
  return props.nodes.map((node) => ({
    id: node.id,
    name: node.label,
    assetId: node.name,
    ...node.info,
  }));
});

const nodesListColumns = computed((): QTableColumn[] => {
  const baseColumns: QTableColumn[] = [
    {
      name: 'name',
      label: 'Name',
      field: 'name',
      align: 'left',
      sortable: true,
    },
    {
      name: 'assetId',
      label: 'Asset ID',
      field: 'assetId',
      align: 'left',
      sortable: true,
    },
  ];

  const metricColumns: QTableColumn[] = metrics.value.map(
    (metric) =>
      ({
        name: metric,
        label: capitalize(metric),
        field: metric,
        format: (value: number) => formatMetricValue(value, metric),
        align: 'right',
        sortable: true,
      }) as QTableColumn,
  );

  return [...baseColumns, ...metricColumns];
});

const sortedNodeOptions = computed((): NodeOption[] => {
  const metric = selectedMetric.value;
  if (!metric) return [];

  return props.nodes
    .map((node) => ({
      id: node.id,
      label: node.label,
      name: node.name,
      metricValue: (node.info?.[metric] as number) || 0,
    }))
    .sort((a, b) => {
      if (isNumber(b.metricValue) && isNumber(a.metricValue)) {
        return b.metricValue - a.metricValue;
      }
      return 0;
    });
});

const selectedNodes = computed((): Node[] => {
  return selectedNodeIds.value.map(
    (option) => props.nodes.find((node) => node.id === option.id)!,
  );
});

const chartSeries = computed(() => {
  return selectedNodes.value.map((node) => {
    if (!node.series) return { name: node.label, data: [] };

    const data = Object.entries(node.series)
      .map(([date, metrics]) => ({
        x: new Date(date).getTime(),
        y: (metrics[selectedMetric.value] as number) || 0,
      }))
      .sort((a, b) => a.x - b.x);

    return {
      name: node.label,
      data,
    };
  });
});

const chartOptions = computed(
  (): ApexOptions => ({
    chart: {
      type: 'line',
      zoom: { enabled: true },
    },
    xaxis: {
      type: 'datetime',
    },
    yaxis: {
      title: {
        text: selectedMetric.value,
      },
      labels: {
        formatter: (val: number) => val.toFixed(2),
      },
    },
  }),
);

const removeNode = (nodeId: number): void => {
  selectedNodeIds.value = selectedNodeIds.value.filter(
    (option) => option.id !== nodeId,
  );
};

const selectNode = (nodeId: number): void => {
  emit('select-node', nodeId);
};
</script>
