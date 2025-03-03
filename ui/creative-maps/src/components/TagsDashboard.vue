<template>
  <q-card class="full-width">
    <q-card-section class="row items-center">
      <div class="text-h6">Tags Metrics Dashboard</div>
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
      <q-table
        v-if="!isDynamicView"
        :rows="tagsMetrics"
        :columns="columns"
        row-key="tag"
        separator="vertical"
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
              <template v-if="col.name === 'tag'">Totals</template>
              <template
                v-else-if="
                  col.name !== 'freq' && totalsRow[col.name] !== undefined
                "
              >
                {{ formatMetricValue(totalsRow[col.name], col.name) }}
              </template>
            </q-td>
          </q-tr>
        </template>
        <template #body-cell-tag="props">
          <q-td :props="props">
            <a
              href="#"
              class="text-primary"
              style="text-decoration: none"
              @click.prevent="onTagClick(props.row)"
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

      <template v-else>
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
              v-model="selectedTags"
              :options="sortedTagOptions"
              multiple
              use-chips
              label="Select tags"
            />
          </div>
        </div>

        <apexchart
          type="line"
          :options="chartOptions"
          :series="chartSeries"
          height="400"
        />
      </template>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, ComputedRef, onMounted } from 'vue';
import { useQuasar, QTableColumn } from 'quasar';
import { TagStats } from './models';
import { capitalize, assertIsError } from 'src/helpers/utils';
import { exportTable } from 'src/helpers/export';
import {
  aggregateNodesMetrics,
  formatMetricValue,
  formatMetricWithProportion,
  getTotalsRow,
} from 'src/helpers/graph';

interface Props {
  tagsStats: TagStats[];
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'select-tag', tagData: TagStats): void;
}>();

const $q = useQuasar();

const isDynamicView = ref(false);
const selectedTags = ref<string[]>([]);
const selectedMetric = ref('');

// get a list of tags for dropdown
const sortedTagOptions = computed(() => {
  if (!selectedMetric.value) return props.tagsStats.map((t) => t.tag);
  return [...props.tagsStats]
    .sort((a, b) => {
      const aValue = a.nodes.reduce(
        (sum, node) =>
          sum + ((node.info?.[selectedMetric.value] as number) || 0),
        0,
      );
      const bValue = b.nodes.reduce(
        (sum, node) =>
          sum + ((node.info?.[selectedMetric.value] as number) || 0),
        0,
      );
      return bValue - aValue;
    })
    .map((t) => t.tag);
});

// Get unique metrics from all nodes
const metrics: ComputedRef<string[]> = computed(() => {
  const metricSet = new Set<string>();
  props.tagsStats.forEach((tagStat) => {
    tagStat.nodes.forEach((node) => {
      if (node.info) {
        Object.keys(node.info).forEach((metric) => metricSet.add(metric));
      }
    });
  });
  return Array.from(metricSet);
});

const totalsRow = computed((): Record<string, number> => {
  return getTotalsRow(
    tagsMetrics.value.map((o) => o.metrics),
    metrics.value,
  );
});

// Initialize with first metric and tag
onMounted(() => {
  if (metrics.value.length) {
    selectedMetric.value = metrics.value[0];
  }
  if (props.tagsStats.length) {
    selectedTags.value = [props.tagsStats[0].tag];
  }
});

// Calculate metrics for each tag
const tagsMetrics = computed(() => {
  return props.tagsStats.map((tagStat) => {
    const metricValues = aggregateNodesMetrics(tagStat.nodes);

    return {
      tag: tagStat.tag,
      freq: tagStat.freq,
      metrics: metricValues,
      nodes: tagStat.nodes,
    };
  });
});

// Define columns dynamically based on metrics
const columns = computed<QTableColumn[]>(() => {
  const baseColumns: QTableColumn[] = [
    {
      name: 'tag',
      label: 'Tag',
      field: 'tag',
      align: 'left',
      sortable: true,
    },
    {
      name: 'freq',
      label: 'Frequency',
      field: 'freq',
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
        field: (row: any) => row.metrics[metric],
        format: (value: number) =>
          formatMetricWithProportion(value, metric, totalsRow.value),
        align: 'right',
        sortable: true,
      }) as QTableColumn,
  );

  return [...baseColumns, ...metricColumns];
});

const onTagClick = (tagData: TagStats) => {
  console.log(tagData);
  emit('select-tag', tagData);
};

const chartSeries = computed(() => {
  return selectedTags.value.map((tag) => {
    console.log('selected: ' + JSON.stringify(tag));
    const tagData = props.tagsStats.find((t) => t.tag === tag);
    if (!tagData) return { name: tag, data: [] };

    // Collect all dates from nodes
    const dateValues = new Map<string, number>();

    tagData.nodes.forEach((node) => {
      if (!node.series) return;

      Object.entries(node.series).forEach(([date, metrics]) => {
        const value = (metrics[selectedMetric.value] as number) || 0;
        dateValues.set(date, (dateValues.get(date) || 0) + value);
      });
    });

    // Convert to sorted array
    const data = Array.from(dateValues.entries())
      .map(([date, value]) => ({
        x: new Date(date).getTime(),
        y: value,
      }))
      .sort((a, b) => a.x - b.x);

    return {
      name: tag,
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

function handleExport() {
  try {
    exportTable(columns.value, tagsMetrics.value, 'tags');
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
