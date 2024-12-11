<template>
  <q-card>
    <q-card-section class="row items-center">
      <div class="text-h6">Clusters Comparison</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>
    <q-card-section class="row items-center">
      <q-btn-toggle
        col="col"
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
              v-model="selectedClusterIds"
              :disable="!selectedMetric"
              :options="sortedClusterOptions"
              multiple
              use-chips
              label="Select clusters"
            />
          </div>
        </div>

        <apexchart
          type="line"
          :options="chartOptions"
          :series="chartSeries"
          height="400"
        />

        <!-- Cluster cards -->
        <div class="row q-gutter-md q-mt-lg">
          <ClusterCard
            v-for="clusterId in selectedClusterIds"
            :key="clusterId"
            :cluster="getClusterById(clusterId)"
            @remove="removeCluster(clusterId)"
            @click="selectCluster(clusterId)"
          />
        </div>
      </template>

      <template v-else>
        <q-table
          :rows="clustersMetrics"
          :columns="clustersListColumns"
          row-key="cluster"
          :pagination="{ rowsPerPage: 0 }"
        >
          <template #body-cell-cluster="props">
            <q-td :props="props">
              <a
                href="#"
                class="text-primary"
                @click.prevent="selectCluster(props.value)"
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
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, ComputedRef } from 'vue';
import ClusterCard from './ClusterCard.vue';
import { ClusterInfo } from './models';
import { assertIsError, capitalize, formatMetricValue } from 'src/helpers/utils';
import { useQuasar, QTableColumn } from 'quasar';
import { isNumber } from 'lodash';
import { exportTable } from 'src/helpers/export';

interface Props {
  clusters: Array<ClusterInfo>;
}
const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'select-cluster', clusterId: string): void;
}>();

const $q = useQuasar();
const isDynamicView = ref(false);
const selectedClusterIds = ref<string[]>([]);
const selectedMetric = ref('');

// Get all available metrics
const metrics = computed(() => {
  const metricSet = new Set<string>();
  props.clusters?.forEach((cluster) => {
    if (cluster.metrics) {
      Object.keys(cluster.metrics).forEach((metric) => metricSet.add(metric));
    }
  });
  return Array.from(metricSet);
});

// Get clusters metrics for static view
const clustersMetrics: ComputedRef<Record<string, number | string>[]> =
  computed(() => {
    if (!props.clusters) return [];
    return props.clusters.map((cluster) => {
      return {
        cluster: cluster.id,
        size: cluster.nodes.length,
        ...cluster.metrics,
      };
    });
  });

// Define columns dynamically based on metrics
const clustersListColumns = computed<QTableColumn[]>(() => {
  const baseColumns: QTableColumn[] = [
    {
      name: 'cluster',
      label: 'Cluster',
      field: 'cluster',
      align: 'left',
      sortable: true,
    },
    {
      name: 'size',
      label: 'Size',
      field: 'size',
      align: 'right',
      sortable: true,
      format: (val) => val.toLocaleString(),
    },
  ];

  // Add a column for each metric
  const metricColumns = metrics.value.map(
    (metric) =>
      ({
        name: metric,
        label: capitalize(metric),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        field: (row: any) => row[metric],
        format: (value: number) => formatMetricValue(value, metric),
        align: 'right',
        sortable: true,
        //classes: 'text-right'
      }) as QTableColumn,
  );

  return [...baseColumns, ...metricColumns];
});

// Return cluster ids as options for dynamic dropdown list
const sortedClusterOptions = computed(() => {
  if (!props.clusters) return [];
  const metric = selectedMetric.value;
  if (!metric) return props.clusters.map((c) => c.id);
  // return clusters ids sorted accordingly to currently selected metric
  return props.clusters
    .map((c) => c.id)
    .sort((a, b) => {
      const aValue =
        props.clusters!.find((cm) => cm.id === a)?.metrics[metric] || 0;
      const bValue =
        props.clusters!.find((cm) => cm.id === b)?.metrics[metric] || 0;
      if (isNumber(bValue) && isNumber(aValue)) {
        return bValue - aValue;
      } else {
        return (bValue as string).length - (aValue as string).length;
      }
    });
});

// Time series data for dynamic view
const chartSeries = computed(() => {
  return selectedClusterIds.value.map((clusterId) => {
    const nodes = props.clusters!.find((n) => n.id === clusterId)?.nodes;
    const dateValues = new Map<string, number>();
    if (!nodes) return {};

    nodes.forEach((node) => {
      if (!node.series) return;

      Object.entries(node.series).forEach(([date, metrics]) => {
        const value = (metrics[selectedMetric.value] as number) || 0;
        dateValues.set(date, (dateValues.get(date) || 0) + value);
      });
    });

    const data = Array.from(dateValues.entries())
      .map(([date, value]) => ({
        x: new Date(date).getTime(),
        y: value,
      }))
      .sort((a, b) => a.x - b.x);

    return {
      name: `Cluster ${clusterId}`,
      data,
    };
  });
});

const chartOptions = computed(() => ({
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
}));

function getClusterById(clusterId: string): ClusterInfo {
  return props.clusters.find((c) => c.id === clusterId)!;
}

function removeCluster(clusterId: string) {
  console.log('remove cluster ' + clusterId);
  selectedClusterIds.value = selectedClusterIds.value.filter(
    (id) => id !== clusterId,
  );
}

function selectCluster(clusterId: string) {
  console.log('select-cluster ' + clusterId);
  emit('select-cluster', clusterId);
}

function handleExport() {
  try {
    exportTable(clustersListColumns.value, clustersMetrics.value, 'clusters');
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
