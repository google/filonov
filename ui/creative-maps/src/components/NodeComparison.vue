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
          <template #header="props">
            <q-tr :props="props">
              <q-th v-for="col in props.cols" :key="col.name" :props="props">
                {{ col.label }}
              </q-th>
            </q-tr>
            <q-tr class="bg-grey-2 text-weight-bold">
              <q-td v-for="col in props.cols" :key="col.name" :props="props">
                <template v-if="col.name === 'name'">Totals</template>
                <template
                  v-else-if="
                    col.name !== 'image' &&
                    col.name !== 'assetId' &&
                    totalsRow[col.name] !== undefined
                  "
                >
                  {{ formatMetricValue(totalsRow[col.name], col.name) }}
                </template>
              </q-td>
            </q-tr>
          </template>
          <template #top-left>
            <div class="row items-center q-mb-md">
              <q-toggle
                v-model="showImages"
                label="Show previews"
                color="primary"
              />
            </div>
          </template>
          <template v-if="showImages" #body-cell-image="props">
            <q-td :props="props">
              <q-img
                :src="props.value"
                spinner-color="primary"
                style="height: 50px; width: 50px; cursor: pointer"
                @click="openPreview(props.row)"
                fit="contain"
              >
                <template #error>
                  <div
                    class="absolute-full flex flex-center bg-negative text-white"
                  >
                    Error
                  </div>
                </template>
              </q-img>
            </q-td>
          </template>
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
          <template #top-right>
            <q-btn
              icon="download"
              color="primary"
              label="Export"
              @click="handleExport"
            />
          </template>
        </q-table>
      </template>
    </q-card-section>
    <q-dialog v-model="showPreview" maximized>
      <CreativePreview
        v-if="previewData"
        :image="previewData.image"
        :media_path="previewData.media_path"
      />
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useQuasar, QTableColumn } from 'quasar';
import type { ApexOptions } from 'apexcharts';
import NodeCard from './NodeCard.vue';
import CreativePreview from './CreativePreview.vue';
import { Node } from './models';
import { assertIsError, capitalize } from 'src/helpers/utils';
import { isNumber } from 'lodash';
import { exportTable } from 'src/helpers/export';
import {
  getTotalsRow,
  formatMetricValue,
  formatMetricWithProportion,
} from 'src/helpers/graph';

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

const $q = useQuasar();
const isDynamicView = ref(false);
const selectedNodeIds = ref<NodeOption[]>([]);
const selectedMetric = ref('');
const showImages = ref(false);
const showPreview = ref(false);
const previewData = ref<{ image: string; media_path: string } | null>(null);

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
    image: node.image,
    media_path: node.media_path,
    assetId: node.name,
    ...node.info,
  }));
});

const totalsRow = computed((): Record<string, number> => {
  return getTotalsRow(nodesMetrics.value, metrics.value);
});

function openPreview(row: NodeMetrics) {
  previewData.value = {
    image: row.image as string,
    media_path: row.media_path as string,
  };
  showPreview.value = true;
}

const nodesListColumns = computed((): QTableColumn[] => {
  const baseColumns: QTableColumn[] = [
    ...(showImages.value
      ? [
          {
            name: 'image',
            label: 'Preview',
            field: 'image',
            align: 'center',
            sortable: false,
          } as QTableColumn,
        ]
      : []),
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
        format: (value: number /*, row: NodeMetrics*/) =>
          formatMetricWithProportion(value, metric, totalsRow.value),
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

function removeNode(nodeId: number) {
  selectedNodeIds.value = selectedNodeIds.value.filter(
    (option) => option.id !== nodeId,
  );
}

function selectNode(nodeId: number) {
  emit('select-node', nodeId);
}

function handleExport() {
  try {
    exportTable(nodesListColumns.value, nodesMetrics.value, 'nodes');
  } catch (error) {
    console.error('Export failed:', error);
    assertIsError(error);
    $q.dialog({
      title: 'Export Error',
      message: `Failed to export table: ${error.message}`,
      color: 'negative',
      persistent: true,
      ok: {
        color: 'primary',
        label: 'Close',
      },
    });
  }
}
</script>
