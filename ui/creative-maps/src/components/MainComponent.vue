<template>
  <div class="main-component q-pa-md">
    <div class="row items-center q-pa-sm bg-grey-2">
      <q-btn
        flat
        icon="upload_file"
        label="Load Data"
        @click="showLoadDataDialog = true"
      >
        <q-tooltip>Load graph data from file or URL</q-tooltip>
      </q-btn>
      <div class="col">
        <template v-if="vertices.length">
          {{ dataSourceDescription }}
          <q-badge class="q-ml-sm"> {{ vertices.length }} nodes </q-badge>
          <q-badge class="q-ml-sm"> {{ edges.length }} edges </q-badge>
        </template>
        <span v-else class="text-grey">No data loaded</span>
      </div>
    </div>
    <div class="row">
      <div class="col-10">
        <d3-graph
          ref="d3GraphRef"
          :vertices="vertices"
          :edges="edges"
          :debug="true"
          class="graph-container"
          @cluster-selected="onClusterSelected"
          @node-selected="onNodeSelected"
        />
      </div>
      <div class="col-2">
        <div class="right-side-menu">
          <q-card>
            <q-tabs
              v-model="activeTab"
              class="text-primary"
              align="justify"
              narrow-indicator
            >
              <q-tab name="info" label="Info" v-if="vertices" />
              <q-tab v-if="selectedCluster" name="metrics" label="Metrics" />
              <q-tab name="tags" label="Tags" v-if="vertices" />
              <q-tab v-if="selectedNode" name="node" label="Node" />
            </q-tabs>

            <q-separator />

            <q-tab-panels v-model="activeTab" animated>
              <q-tab-panel name="info">
                <div class="text-h6">Global Statistics</div>

                <!-- Basic stats -->
                <div class="row q-gutter-md q-mb-lg">
                  <q-card class="col">
                    <q-card-section>
                      <div class="text-subtitle2">Total Clusters</div>
                      <div class="text-h4">{{ clusterIds.length }}</div>
                    </q-card-section>
                  </q-card>

                  <q-card class="col">
                    <q-card-section>
                      <div class="text-subtitle2">Total Nodes</div>
                      <div class="text-h4">{{ vertices.length }}</div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Cluster sizes histogram -->
                <q-card>
                  <q-card-section>
                    <div class="text-subtitle2">Cluster Sizes Distribution</div>
                    <metric-histogram
                      :data="getClusterSizesHistogramData"
                      metric="Cluster Size"
                    />
                  </q-card-section>
                </q-card>

                <!-- Compare clusters button -->
                <q-btn
                  color="primary"
                  label="Compare Clusters"
                  icon="compare"
                  class="q-mt-md"
                  @click="showClusterComparison = true"
                />
              </q-tab-panel>

              <q-tab-panel v-if="selectedCluster" name="metrics">
                <div class="text-h6">Cluster Metrics</div>
                <q-list separator>
                  <q-item>
                    <q-item-section>
                      <q-item-label>Nodes</q-item-label>
                      <q-item-label caption>{{
                        selectedCluster.nodeCount
                      }}</q-item-label>
                    </q-item-section>
                  </q-item>
                  <q-separator spaced />
                </q-list>
                <q-list separator>
                  <q-item
                    v-for="(value, metric) in selectedCluster.metrics"
                    :key="metric"
                  >
                    <q-item-section>
                      <div class="row items-center">
                        <q-item-label class="q-mr-sm">{{
                          metric
                        }}</q-item-label>
                        <q-btn
                          flat
                          round
                          dense
                          size="sm"
                          icon="show_chart"
                          @click="doShowTimeSeriesDialog(metric)"
                        >
                          <q-tooltip anchor="bottom middle" self="top middle">
                            Open time series chart
                          </q-tooltip>
                        </q-btn>
                      </div>
                      <q-item-label caption>{{
                        formatMetricValue(value, metric.toString())
                      }}</q-item-label>
                      <metric-histogram
                        :data="getHistogramData(metric.toString())"
                        :metric="metric.toString()"
                        @metric-clicked="onClusterHistogramMetricClicked"
                      />
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-tab-panel>

              <q-tab-panel name="tags" v-if="sortedTags.length">
                <div class="text-h6">
                  {{ selectedCluster ? 'Cluster Tags' : 'All Tags' }}
                </div>
                <q-space />
                <q-btn
                  flat
                  icon="dashboard"
                  label="Tags Dashboard"
                  @click="showTagsDashboardDialog = true"
                >
                  <q-tooltip>Show metrics by tag</q-tooltip>
                </q-btn>
                <q-list separator>
                  <q-item v-for="tagInfo in sortedTags" :key="tagInfo.tag">
                    <q-item-section>
                      <q-item-label>
                        <a
                          href="#"
                          class="text-primary"
                          style="text-decoration: none"
                          @click.prevent="highlightNodesByTag(tagInfo)"
                        >
                          {{ tagInfo.tag }}
                        </a>
                      </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-chip size="sm" color="primary" text-color="white">
                        {{ tagInfo.freq }}
                      </q-chip>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-tab-panel>

              <q-tab-panel name="node" v-if="selectedNode">
                <node-card :node="selectedNode" :noClose="true" />
              </q-tab-panel>
            </q-tab-panels>
            <!-- Time Series Dialog -->
            <q-dialog
              v-model="showTimeSeriesDialog"
              maximized
              transition-show="slide-up"
              transition-hide="slide-down"
            >
              <q-card class="full-width">
                <q-card-section class="row items-center">
                  <div class="text-h6">{{ selectedMetric }} over time</div>
                  <q-space />
                  <q-btn icon="close" flat round dense v-close-popup />
                </q-card-section>

                <q-card-section>
                  <time-series-chart
                    :data="timeSeriesData"
                    :metric="selectedMetric"
                    :cluster-nodes="selectedCluster!.nodes"
                    :height="400"
                  />
                </q-card-section>
              </q-card>
            </q-dialog>
            <!-- Tags Dashboard Dialog -->
            <q-dialog
              v-model="showTagsDashboardDialog"
              maximized
              transition-show="slide-up"
              transition-hide="slide-down"
            >
              <tags-dashboard
                :tags-stats="sortedTags"
                @select-tag="onTagDashboardSelect"
              />
            </q-dialog>
            <!-- Clusters Comparison Dialog -->
            <q-dialog
              v-model="showClusterComparison"
              maximized
              transition-show="slide-up"
              transition-hide="slide-down"
            >
              <cluster-comparison
                :vertices="vertices"
                :clusterIds="clusterIds"
                @select-cluster="selectCluster"
              ></cluster-comparison>
            </q-dialog>
          </q-card>
        </div>
      </div>
    </div>

    <q-dialog v-model="showLoadDataDialog">
      <q-card style="min-width: 500px; height: auto">
        <q-card-section class="row items-center">
          <div class="text-h6">Load Graph Data</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <json-file-selector @json-loaded="onDataLoaded" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import * as d3 from 'd3';
import D3Graph from 'components/D3Graph.vue';
import JsonFileSelector from 'components/JsonFileSelector.vue';
import MetricHistogram from './MetricHistogram.vue';
import TimeSeriesChart from './TimeSeriesChart.vue';
import TagsDashboard from './TagsDashboard.vue';
import NodeCard from './NodeCard.vue';
import ClusterComparison from './ClusterComparison.vue';
import {
  Node,
  Edge,
  GraphData,
  ClusterInfo,
  TagStats,
  AbstractNode,
} from 'components/models';
import { formatMetricValue } from 'src/helpers/utils';

const d3GraphRef = ref<InstanceType<typeof D3Graph> | null>(null);
const showLoadDataDialog = ref(false);
const dataSourceDescription = ref('');
const vertices = ref([] as Node[]);
const edges = ref([] as Edge[]);
const selectedCluster = ref(null as ClusterInfo | null);
const selectedNode = ref(null as Node | null);
const activeTab = ref('info');
const showClusterComparison = ref(false);
const showTimeSeriesDialog = ref(false);
const showTagsDashboardDialog = ref(false);
const selectedMetric = ref('');
const clusterIds = ref([] as string[]);

const sortedTags = computed(() => {
  if (!selectedCluster.value) {
    // Global scope - collect tags from all vertices
    return collectTags(vertices.value);
  }
  return collectTags(selectedCluster.value.nodes);
});

const timeSeriesData = computed(() => {
  if (!selectedCluster.value || !selectedMetric.value) return [];

  // Transform cluster nodes' series data
  const allSeries = selectedCluster.value.nodes.flatMap((node: Node) => {
    return Object.entries(node.series || {}).map(([date, metrics]) => ({
      date: new Date(date),
      value: metrics[selectedMetric.value] || 0,
    }));
  });
  if (!allSeries.length) {
    console.log('selectedCluster has no time series');
  }
  // Aggregate by date
  const aggregated = d3.rollup(
    allSeries,
    (v) => d3.sum(v, (d) => d.value as number),
    (d) => d.date.getTime(),
  );

  return Array.from(aggregated, ([date, value]) => ({
    date: new Date(date),
    value,
  })).sort((a, b) => a.date.valueOf() - b.date.valueOf());
});

async function onDataLoaded(args: { data: GraphData; origin: string }) {
  const jsonData: GraphData = args.data;
  vertices.value = jsonData.nodes;
  edges.value = jsonData.edges;
  clusterIds.value = Array.from(
    new Set(vertices.value.map((node) => node.cluster)),
  ).sort();
  showLoadDataDialog.value = false;
  dataSourceDescription.value = args.origin || 'Custom data';
}

function collectTags(nodes: Node[]): TagStats[] {
  const tagsMap = new Map<string, { freq: number; nodes: Node[] }>();

  nodes.forEach((node: Node) => {
    node.tags?.forEach((tagInfo) => {
      if (!tagsMap.has(tagInfo.tag)) {
        tagsMap.set(tagInfo.tag, { freq: 0, nodes: [] });
      }
      const stats = tagsMap.get(tagInfo.tag)!;
      stats.freq += 1;
      stats.nodes.push(node);
    });
  });

  return Array.from(tagsMap.entries())
    .map(([tag, stats]) => ({
      tag,
      freq: stats.freq,
      nodes: stats.nodes,
    }))
    .sort((a, b) => b.freq - a.freq); // Sort by frequency descending
}

function highlightNodesByTag(tagStat: TagStats) {
  // Get nodes that have this tag
  const nodesWithTag = tagStat.nodes;

  // Use the D3Graph method to highlight these nodes
  d3GraphRef.value?.setCurrentCluster(nodesWithTag);
}

function onTagDashboardSelect(tagStat: TagStats) {
  showTagsDashboardDialog.value = false;
  console.log('onTagDashboardSelect ' + tagStat);
  d3GraphRef.value?.setCurrentCluster(tagStat.nodes);
}

function onNodeSelected(node: Node) {
  selectedNode.value = node;
}

function onClusterSelected(cluster: ClusterInfo) {
  if (cluster) {
    selectedCluster.value = cluster;
  } else {
    selectedCluster.value = null;
    if (activeTab.value !== 'tags' && activeTab.value !== 'info') {
      activeTab.value = 'tags';
    }
  }
}
function selectCluster(clusterId: string) {
  showClusterComparison.value = false;
  d3GraphRef.value?.onClusterSelect(clusterId);
}

function getHistogramData(metric: string) {
  if (selectedCluster.value) {
    return createHistogramData(selectedCluster.value.nodes, metric);
  }
}

const clusterSizes = computed(() => {
  const sizes = new Map<string, number>();
  vertices.value.forEach((node) => {
    if (node.cluster) {
      sizes.set(node.cluster, (sizes.get(node.cluster) || 0) + 1);
    }
  });
  return sizes;
});

const getClusterSizesHistogramData = computed(() => {
  // Create nodes-like array where each entry represents a cluster with its size as a metric
  const clusterSizeNodes = Array.from(clusterSizes.value.entries()).map(
    ([clusterId, size]) => ({
      info: { size }, // Treat size as a metric
      id: clusterId,
    }),
  );

  return createHistogramData(clusterSizeNodes, 'size');
});

function createHistogramData(nodes: AbstractNode[], metric: string) {
  if (!nodes || nodes.length === 0) return [];

  // Get all values of the metric
  const values = nodes
    .map((node) => ({ value: node.info?.[metric] as number, node }))
    .filter((v) => v.value !== undefined && v.value !== null);

  if (!values || values.length === 0) return [];

  // Create bin generator
  const binner = d3
    .bin<{ value: number; node: AbstractNode }, number>()
    .value((d) => d.value)
    .domain([d3.min(values, (d) => d.value)!, d3.max(values, (d) => d.value)!])
    .thresholds(10); // number of bins

  // Generate bins
  const bins = binner(values);

  return bins.map((bin) => ({
    x0: bin.x0,
    x1: bin.x1,
    count: bin.length,
    nodes: bin.map((d) => d.node),
  }));
}

function onClusterHistogramMetricClicked(args: {
  metric: string;
  nodes: Node[];
}) {
  if (d3GraphRef.value) {
    d3GraphRef.value.highlightNodes(args.nodes);
  }
}

function doShowTimeSeriesDialog(metric: string) {
  selectedMetric.value = metric;
  showTimeSeriesDialog.value = true;
}
</script>
<style scoped>
.right-side-menu {
  height: 100%;
}

.q-card {
  height: 100%;
}

.q-tab-panel {
  padding: 16px;
}

.text-h6 {
  margin-bottom: 16px;
}
</style>
