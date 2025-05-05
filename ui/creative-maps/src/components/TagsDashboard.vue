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
          <div class="col-auto q-mt-md">
            <q-btn
              label="Clear Chart"
              flat
              @click="selectedTags = []"
              icon="clear"
              :disable="selectedTags.length === 0"
            />
          </div>
        </div>
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-12">
            <q-expansion-item
              expand-separator
              icon="trending_up"
              label="Trend Detection"
              default-opened
            >
              <div class="q-pa-md">
                <div class="row q-col-gutter-md">
                  <div class="col-auto">
                    <q-select
                      v-model="trendType"
                      :options="[
                        { label: 'All Trends', value: 'all' },
                        { label: 'Growth', value: 'growth' },
                        { label: 'Decline', value: 'decline' },
                      ]"
                      option-value="value"
                      label="Trend Type"
                      dense
                      options-dense
                      style="width: 120px"
                    />
                  </div>
                  <div class="col-auto">
                    <q-input
                      v-model.number="thresholdPercent"
                      type="number"
                      label="Threshold %"
                      min="1"
                      max="100"
                      dense
                      style="width: 120px"
                    />
                  </div>
                  <div class="col-auto">
                    <q-input
                      v-model.number="maWindowSize"
                      type="number"
                      label="MA window size"
                      min="1"
                      max="30"
                      title="Controls how many days are used to calculate moving average. Smaller values detect shorter trends, larger values filter out noise."
                      dense
                      style="width: 120px"
                    />
                  </div>
                  <div class="col-auto">
                    <q-input
                      v-model.number="maxTrendsToShow"
                      type="number"
                      label="Max Trends"
                      min="1"
                      dense
                      style="width: 120px"
                    />
                  </div>
                  <div class="col-auto self-end">
                    <q-btn
                      color="primary"
                      label="Detect Trends"
                      @click="detectTrends"
                      :loading="detectingTrends"
                      icon="search"
                    />
                  </div>
                </div>

                <div v-if="topTrends.length > 0" class="q-mt-md">
                  <q-table
                    :rows="topTrends"
                    :columns="trendColumns"
                    row-key="tag"
                    dense
                    class="trend-table"
                    :pagination="{ rowsPerPage: 10 }"
                  >
                    <template #body-cell-tag="props">
                      <q-td :props="props">
                        <div class="row items-center">
                          <q-checkbox
                            v-model="selectedTrendTags"
                            :val="props.row.tag"
                            class="q-mr-sm"
                          />
                          {{ props.value }}
                        </div>
                      </q-td>
                    </template>
                    <template #body-cell-trendType="props">
                      <q-td :props="props">
                        <q-chip
                          :color="
                            props.value === 'growth' ? 'positive' : 'negative'
                          "
                          text-color="white"
                          dense
                          class="q-px-sm"
                        >
                          <q-icon
                            :name="
                              props.value === 'growth'
                                ? 'trending_up'
                                : 'trending_down'
                            "
                            class="q-mr-xs"
                          />
                          {{ capitalize(props.value) }}
                        </q-chip>
                      </q-td>
                    </template>
                    <template #body-cell-changePercent="props">
                      <q-td :props="props">
                        <span
                          :class="
                            props.value >= 0 ? 'text-positive' : 'text-negative'
                          "
                        >
                          {{ props.value >= 0 ? '+' : ''
                          }}{{ props.value.toFixed(2) }}%
                        </span>
                      </q-td>
                    </template>
                    <template #top>
                      <div class="row full-width items-center">
                        <div class="col-auto text-subtitle1">Top Trends</div>
                        <div class="col-auto q-ml-md">
                          <q-btn
                            label="Add Selected to Chart"
                            color="secondary"
                            size="sm"
                            @click="addSelectedTrendsToChart"
                            icon="add_chart"
                            :disable="selectedTrendTags.length === 0"
                          />
                        </div>
                      </div>
                    </template>
                  </q-table>
                </div>
                <div v-else-if="detectingTrends" class="text-center q-py-md">
                  <q-spinner color="primary" size="2em" />
                  <div class="q-mt-sm text-caption">Analyzing trends...</div>
                </div>
                <div
                  v-else-if="trendsDetectionRun && topTrends.length === 0"
                  class="text-center q-py-md"
                >
                  <q-icon name="info" color="grey-7" size="2em" />
                  <div class="q-mt-sm text-caption">
                    No significant trends found with current settings
                  </div>
                </div>
              </div>
            </q-expansion-item>
          </div>
        </div>

        <apexchart :options="chartOptions" :series="chartSeries" height="400" />

        <div class="q-mt-lg">
          <div class="row items-center q-mb-md">
            <div class="text-subtitle1">Selected Tags Details</div>
            <q-space />
          </div>
          <div class="row q-gutter-md q-mt-sm">
            <div v-for="tag in selectedTags" :key="tag" class="col-auto">
              <TagCard
                :tagData="getTagData(tag)"
                :selectedMetric="selectedMetric"
                @remove="removeTag(tag)"
                @view-nodes="viewTagNodesInGraph(tag)"
              />
            </div>
          </div>
          <div
            v-if="selectedTags.length === 0"
            class="text-center q-py-lg text-grey"
          >
            <q-icon name="info" size="2em" />
            <div class="q-mt-sm">
              Select tags from the dropdown above to view details
            </div>
          </div>
        </div>

        <!-- Common Nodes Analysis Panel -->
        <q-card v-if="selectedTags.length > 0" class="q-mt-md">
          <q-card-section class="bg-grey-2">
            <div class="row items-center">
              <div class="text-subtitle1">Common Nodes Analysis</div>
              <q-space />
            </div>
          </q-card-section>

          <q-card-section>
            <div class="row items-center q-mb-md">
              <div class="col text-body1">
                <span class="text-weight-bold">{{ commonNodes.length }}</span>
                common nodes found in selected tags:
                <q-chip
                  v-for="tag in selectedTags"
                  :key="tag"
                  color="primary"
                  text-color="white"
                  dense
                  class="q-ml-xs"
                >
                  {{ tag }}
                </q-chip>
              </div>
              <div class="col-auto">
                <q-btn
                  color="primary"
                  icon="visibility"
                  label="View In Graph"
                  :disable="commonNodes.length === 0"
                  @click="viewCommonNodesInGraph"
                />
              </div>
            </div>

            <!-- Mini table of common nodes -->
            <q-table
              v-if="commonNodes.length > 0"
              :rows="commonNodes"
              :columns="commonNodesColumns"
              row-key="id"
              dense
              :pagination="{ rowsPerPage: 5 }"
            >
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
              <template #body-cell-label="props">
                <q-td :props="props">
                  <a
                    href="#"
                    class="text-primary"
                    @click.prevent="selectNode(props.row)"
                  >
                    {{ props.value }}
                  </a>
                </q-td>
              </template>
              <template v-if="selectedMetric" #body-cell-metric="props">
                <q-td :props="props">
                  {{
                    formatMetricValue(
                      props.row.info?.[selectedMetric] || 0,
                      selectedMetric,
                    )
                  }}
                </q-td>
              </template>
            </q-table>

            <div v-else class="text-center q-py-md text-grey">
              <q-icon name="info" size="2em" />
              <div class="q-mt-sm">
                No common nodes found between selected tags
              </div>
            </div>
          </q-card-section>
        </q-card>
      </template>
    </q-card-section>
  </q-card>
  <q-dialog v-model="showPreview" maximized>
    <CreativePreview
      v-if="previewData"
      :image="previewData.image"
      :media_path="previewData.media_path"
    />
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, ComputedRef, onMounted, watch } from 'vue';
import { useQuasar, QTableColumn } from 'quasar';
import { TagStats, TagStatsWithMetrics, Node } from './models';
import { capitalize, assertIsError } from 'src/helpers/utils';
import { exportTable } from 'src/helpers/export';
import TagCard from 'components/TagCard.vue';
import CreativePreview from './CreativePreview.vue';

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
  (e: 'select-nodes', nodes: Node[]): void;
}>();

const $q = useQuasar();

const isDynamicView = ref(false);
const selectedTags = ref<string[]>([]);
const selectedMetric = ref('');
const showImages = ref(false);
const showPreview = ref(false);
const previewData = ref<{ image: string; media_path: string } | null>(null);

// Trend detection parameters
const trendType = ref('all');
const thresholdPercent = ref(15);
const maWindowSize = ref(3);
const maxTrendsToShow = ref(10);
const detectingTrends = ref(false);
const trendsDetectionRun = ref(false);
const topTrends = ref<TrendResult[]>([]);
const selectedTrendTags = ref<string[]>([]);

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
    selectedTags.value = [sortedTagOptions.value[0]];
  }
});

// Calculate metrics for each tag
const tagsMetrics = computed<TagStatsWithMetrics[]>(() => {
  return props.tagsStats.map((tagStat) => {
    const metricValues = aggregateNodesMetrics(tagStat.nodes);

    return {
      tag: tagStat.tag,
      freq: tagStat.freq,
      avgScore: tagStat.avgScore,
      metrics: metricValues,
      nodes: tagStat.nodes,
    };
  });
});

function openPreview(row: Node) {
  previewData.value = {
    image: row.image as string,
    media_path: row.media_path as string,
  };
  showPreview.value = true;
}

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
    {
      name: 'avgScore',
      label: 'Avg. Score',
      field: 'avgScore',
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

const trendColumns = computed<QTableColumn[]>(() => {
  return [
    {
      name: 'tag',
      label: 'Tag',
      field: 'tag',
      align: 'left',
      sortable: true,
    },
    {
      name: 'trendType',
      label: 'Trend',
      field: 'trendType',
      align: 'center',
      sortable: false,
    },
    {
      name: 'changePercent',
      label: 'Change %',
      field: 'changePercent',
      align: 'right',
      sortable: true,
    },
    {
      name: 'changeAbs',
      label: 'Change abs.',
      field: (row) => (row.endValue - row.startValue).toFixed(2),
      align: 'right',
      sortable: true,
    },
    {
      name: 'period',
      label: 'Period',
      field: (row) =>
        `${formatDate(row.startDate)} - ${formatDate(row.endDate)}`,
      align: 'right',
    },
  ];
});

function onTagClick(tagData: TagStats) {
  emit('select-tag', tagData);
}

function getTagData(tagName: string): TagStatsWithMetrics {
  return tagsMetrics.value.find((t) => t.tag === tagName)!;
}

// Compute common nodes between selected tags
const commonNodes = computed((): Node[] => {
  if (selectedTags.value.length === 0) return [];

  // Get nodes from the first selected tag
  const firstTagNodes = getTagData(selectedTags.value[0]).nodes;

  if (selectedTags.value.length === 1) return firstTagNodes;

  // Find intersection with other selected tags
  return firstTagNodes.filter((node) => {
    return selectedTags.value.slice(1).every((tag) => {
      const tagData = getTagData(tag);
      return tagData.nodes.some((n) => n.id === node.id);
    });
  });
});

// Columns for the common nodes table
const commonNodesColumns = computed((): QTableColumn[] => {
  const columns: QTableColumn[] = [
    {
      name: 'image',
      label: 'Preview',
      field: 'image',
      align: 'left',
    },
    {
      name: 'label',
      label: 'Name',
      field: 'label',
      align: 'left',
      sortable: true,
    },
  ];

  // Add column for selected metric
  if (selectedMetric.value) {
    columns.push({
      name: 'metric',
      label: capitalize(selectedMetric.value),
      field: (row: Node) => row.info?.[selectedMetric.value] || 0,
      align: 'right',
      sortable: true,
    });
  }

  return columns;
});

// remove a tag from the selected tags
function removeTag(tagName: string) {
  selectedTags.value = selectedTags.value.filter((tag) => tag !== tagName);
}

// View nodes for a specific tag in the main graph
function viewTagNodesInGraph(tagName: string) {
  const tagData = getTagData(tagName);
  emit('select-tag', tagData);
}

// View common nodes in the main graph
function viewCommonNodesInGraph() {
  emit('select-nodes', commonNodes.value);
}

function selectNode(node: Node) {
  emit('select-nodes', [node]);
}

const chartSeries = computed(() => {
  return selectedTags.value.map((tag) => {
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
    animations: {
      enabled: true,
      easing: 'easeinout',
      speed: 800,
    },
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
  tooltip: {
    shared: true,
    intersect: false,
    x: {
      format: 'yyyy-MM-dd',
    },
  },
  legend: {
    position: 'bottom',
    horizontalAlign: 'right',
  },
  stroke: {
    width: 2,
    curve: 'smooth',
  },
  markers: {
    size: 4,
    hover: {
      size: 6,
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

// Trend Detection Functions
interface TrendResult {
  tag: string;
  metric: string;
  trendType: 'growth' | 'decline' | 'stable';
  changePercent: number;
  startValue: number;
  endValue: number;
  startDate: Date;
  endDate: Date;
}

// For each tag, construct a properly ordered time series with no gaps
function prepareTimeSeriesData(
  tagData: TagStats,
  metric: string,
): { date: Date; value: number }[] {
  // Collect all dates from nodes with their values
  const dateValues = new Map<string, number>();

  tagData.nodes.forEach((node) => {
    if (!node.series) return;

    Object.entries(node.series).forEach(([dateStr, metrics]) => {
      const value = (metrics[metric] as number) || 0;
      dateValues.set(dateStr, (dateValues.get(dateStr) || 0) + value);
    });
  });

  // Convert to sorted array
  const sortedData = Array.from(dateValues.entries())
    .map(([dateStr, value]) => ({
      date: new Date(dateStr),
      value,
    }))
    .sort((a, b) => a.date.getTime() - b.date.getTime());

  return sortedData;
}

function calculateMovingAverage(
  data: { date: Date; value: number }[],
  windowSize: number,
): { date: Date; value: number; ma: number }[] {
  return data.map((point, index) => {
    // Calculate the start index for the window
    const startIdx = Math.max(0, index - windowSize + 1);
    // Get the window of data points
    const window = data.slice(startIdx, index + 1);
    // Calculate average
    const sum = window.reduce((acc, curr) => acc + curr.value, 0);
    const ma = window.length > 0 ? sum / window.length : point.value;

    return {
      date: point.date,
      value: point.value,
      ma,
    };
  });
}

/**
 * Simple trend detection using moving averages
 */
function detectTrend(
  tagData: TagStats,
  metric: string,
  thresholdPercent: number = 15,
  maWindow = 3,
): TrendResult | null {
  // Get prepared time series data
  const timeSeriesData = prepareTimeSeriesData(tagData, metric);

  // Need at least 5 data points for reliable detection
  if (timeSeriesData.length < 5) {
    return null;
  }

  // Sort data by date
  const sortedData = [...timeSeriesData].sort(
    (a, b) => a.date.getTime() - b.date.getTime(),
  );

  // Calculate moving average (3-day window)
  const smoothedData = calculateMovingAverage(sortedData, maWindow);

  // We need at least 5 points with moving averages
  if (smoothedData.length < 5) {
    return null;
  }

  // Find the most significant trend within the data
  // Look at all possible periods of at least 3 days
  let maxChangePercent = 0;
  let trendStartIndex = 2; // Start from 3rd point (first with reliable MA)
  let trendEndIndex = smoothedData.length - 1;

  // Examine all possible periods looking for the most significant change
  for (let startIdx = 2; startIdx < smoothedData.length - 2; startIdx++) {
    for (let endIdx = startIdx + 2; endIdx < smoothedData.length; endIdx++) {
      const periodStartValue = smoothedData[startIdx].ma;
      const periodEndValue = smoothedData[endIdx].ma;

      // Skip if start value is zero to avoid division by zero
      if (periodStartValue === 0) continue;

      const periodChangePercent =
        ((periodEndValue - periodStartValue) / periodStartValue) * 100;

      // If we found a more significant change, record it
      if (Math.abs(periodChangePercent) > Math.abs(maxChangePercent)) {
        maxChangePercent = periodChangePercent;
        trendStartIndex = startIdx;
        trendEndIndex = endIdx;
      }
    }
  }

  // Get the start and end points of the most significant period
  const startPoint = smoothedData[trendStartIndex];
  const endPoint = smoothedData[trendEndIndex];

  // Calculate change for the most significant period
  const startValue = startPoint.ma;
  const endValue = endPoint.ma;
  const changePercent = maxChangePercent;

  // Determine trend type
  let trendType: 'growth' | 'decline' | 'stable' = 'stable';
  if (Math.abs(changePercent) >= thresholdPercent) {
    trendType = changePercent > 0 ? 'growth' : 'decline';
  }

  return {
    tag: tagData.tag,
    metric,
    trendType,
    changePercent,
    startValue,
    endValue,
    startDate: startPoint.date,
    endDate: endPoint.date,
  };
}

function formatDate(date: Date): string {
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

async function detectTrends() {
  detectingTrends.value = true;
  trendsDetectionRun.value = true;
  selectedTrendTags.value = [];

  try {
    console.log(
      `Starting trend detection with type filter: ${trendType.value}`,
    );
    console.log(`Threshold: ${thresholdPercent.value}%`);

    // Get trends for all tags using our simplified algorithm
    const allTrends = props.tagsStats
      .map((tagData) =>
        detectTrend(
          tagData,
          selectedMetric.value,
          thresholdPercent.value,
          maWindowSize.value,
        ),
      )
      .filter((trend): trend is TrendResult => trend !== null);

    console.log(`Found ${allTrends.length} trends in total`);

    // Apply filter based on selected trend type
    let filteredTrends = allTrends;
    if (trendType.value !== 'all') {
      // Extract the string value from the object if needed
      const filterValue =
        typeof trendType.value === 'object' && trendType.value !== null
          ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (trendType.value as any).value // Get the value property from the object
          : trendType.value;

      filteredTrends = allTrends.filter(
        (trend) => trend.trendType === filterValue,
      );
    }

    // Sort by absolute percentage change
    // const sortedTrends = filteredTrends.sort(
    //   (a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent),
    // );
    const sortedTrends = filteredTrends.sort(
      (a, b) =>
        Math.abs(b.endValue - b.startValue) -
        Math.abs(a.endValue - a.startValue),
    );
    // Get top trends
    topTrends.value = sortedTrends.slice(0, maxTrendsToShow.value);
    console.log(`Showing top ${topTrends.value.length} trends`);

    // Log the trends being displayed
    if (topTrends.value.length > 0) {
      topTrends.value.forEach((trend) => {
        console.log(
          `${trend.tag}: ${trend.trendType}, ${trend.changePercent.toFixed(2)}%, ${trend.endValue - trend.startValue}`,
        );
      });
    } else {
      console.log('No trends to display after filtering');
    }
  } catch (error) {
    console.error('Error detecting trends:', error);
    $q.notify({
      color: 'negative',
      message: 'Error detecting trends',
      icon: 'error',
    });
  } finally {
    detectingTrends.value = false;
  }
}

function addSelectedTrendsToChart() {
  // Get current selected tags
  const currentTags = new Set(selectedTags.value);

  // Add selected trend tags
  selectedTrendTags.value.forEach((tag) => {
    currentTags.add(tag);
  });

  selectedTags.value = Array.from(currentTags);

  // Clear selected trend tags
  selectedTrendTags.value = [];
}

// Reset trends when metric changes
watch(selectedMetric, () => {
  topTrends.value = [];
  trendsDetectionRun.value = false;
});
</script>
<style>
.trend-table .q-table__top {
  padding-top: 8px;
  padding-bottom: 8px;
}
</style>
