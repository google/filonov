<template>
  <div class="main-component q-pa-md">
    <div class="row items-center q-pa-sm bg-grey-2 controls-bar">
      <q-btn
        flat
        icon="upload_file"
        label="Load Data"
        @click="showLoadDataDialog = true"
      >
        <q-tooltip>Load graph data from file or URL</q-tooltip>
      </q-btn>
      <div class="col">
        <template v-if="nodes.length">
          {{ dataSourceDescription }}
          <q-badge class="q-ml-sm"> {{ nodes.length }} nodes </q-badge>
          <q-badge class="q-ml-sm"> {{ edges.length }} edges </q-badge>
        </template>
        <span v-else class="text-grey">No data loaded</span>
      </div>
      <q-btn v-if="nodes.length" flat @click="unloadData">Unload</q-btn>
    </div>
    <div class="row content-area">
      <div class="col-9 graph-container">
        <d3-graph
          ref="d3GraphRef"
          :nodes="nodes"
          :edges="edges"
          :clusters="clusters"
          :debug="true"
          class="graph-container"
          @cluster-selected="onClusterSelected"
          @node-selected="onNodeSelected"
        />
      </div>
      <div class="col-3 side-menu-container">
        <div class="side-menu">
          <q-card class="menu-card" flat bordered>
            <q-item>
              <q-breadcrumbs class="items-center">
                <template
                  v-for="(item, index) in history.breadcrumbs.value"
                  :key="index"
                >
                  <!-- Regular breadcrumb item -->
                  <q-breadcrumbs-el
                    class="text-h7 text-bold"
                    v-if="!item.isDropdown"
                    clickable
                    @click="item.onClick"
                    :label="item.description"
                    :class="[
                      'text-h7 text-bold',
                      index !== history.breadcrumbs.value.length - 1
                        ? 'cursor-pointer'
                        : '',
                    ]"
                  />
                  <!-- Dropdown for intermediate steps -->
                  <q-btn-dropdown
                    v-else
                    flat
                    label="..."
                    class="q-breadcrumbs__el text-h7"
                  >
                    <q-list>
                      <q-item
                        v-for="subItem in item.items"
                        :key="subItem.description"
                        class="text-h7 text-bold"
                        clickable
                        v-close-popup
                        @click="subItem.onClick"
                      >
                        <q-item-section>{{
                          subItem.description
                        }}</q-item-section>
                      </q-item>
                    </q-list>
                  </q-btn-dropdown>
                </template>
              </q-breadcrumbs>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label>Node count</q-item-label>
                <q-item-label caption>{{
                  selectedCluster?.nodes.length || nodes.length
                }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-tabs
              v-model="activeTab"
              class="text-primary"
              align="justify"
              narrow-indicator
            >
              <q-tab v-if="nodes" name="info" label="Info" />
              <q-tab v-if="nodes.length" name="metrics" label="Metrics" />
              <q-tab v-if="nodes.length" name="tags" label="Tags" />
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
                      <div class="text-h4">{{ clusters.length }}</div>
                    </q-card-section>
                  </q-card>

                  <q-card class="col">
                    <q-card-section>
                      <div class="text-subtitle2">Total Nodes</div>
                      <div class="text-h4">{{ nodes.length }}</div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Cluster sizes histogram -->
                <q-card>
                  <q-card-section>
                    <div class="text-subtitle2">Cluster Sizes Distribution</div>
                    <MetricHistogram
                      :data="getClusterSizesHistogramData"
                      metric="Cluster Size"
                      @metric-clicked="onClusterHistogramMetricClicked"
                    />
                  </q-card-section>
                </q-card>

                <!-- Compare clusters button -->
                <div class="row q-gutter-md">
                  <div class="col">
                    <q-btn
                      v-if="clusters.length"
                      color="primary"
                      label="Compare Clusters"
                      icon="compare"
                      class="q-mt-md"
                      @click="showClusterComparison = true"
                      style="width: 100%"
                    />
                  </div>
                </div>
                <div class="row q-gutter-md">
                  <div class="col">
                    <q-btn
                      v-if="nodes.length"
                      color="primary"
                      label="Compare Nodes"
                      icon="compare_arrows"
                      class="q-mt-md"
                      @click="showNodeComparison = true"
                      style="width: 100%"
                    />
                  </div>
                </div>
              </q-tab-panel>

              <q-tab-panel name="metrics">
                <q-list separator v-if="selectedCluster">
                  <q-item
                    v-for="(value, metric) in selectedCluster?.metrics"
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
                      <MetricHistogram
                        :data="getHistogramData(metric.toString())"
                        :metric="metric.toString()"
                        @metric-clicked="onClusterHistogramMetricClicked"
                      />
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-tab-panel>

              <q-tab-panel name="tags" v-if="sortedTags.length">
                <div class="text-h6">Tags ({{ sortedTags.length }})</div>
                <q-space />
                <q-btn
                  flat
                  icon="dashboard"
                  label="Tags Dashboard"
                  @click="showTagsDashboardDialog = true"
                >
                  <q-tooltip>Show metrics by tag</q-tooltip>
                </q-btn>

                <!-- Search input -->
                <q-input
                  v-model="tagSearchQuery"
                  dense
                  clearable
                  placeholder="Search tags"
                  class="q-mb-md"
                  @clear="tagSearchQuery = ''"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                  <template v-slot:append v-if="tagSearchQuery">
                    <q-badge color="primary" text-color="white">
                      {{ filteredTags.length }}/{{ sortedTags.length }}
                    </q-badge>
                  </template>
                </q-input>

                <q-list separator>
                  <q-item v-for="tagInfo in filteredTags" :key="tagInfo.tag">
                    <q-item-section>
                      <q-item-label>
                        <a
                          href="#"
                          class="text-primary"
                          style="text-decoration: none"
                          @click.prevent="selectNodesByTag(tagInfo)"
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
                <NodeCard
                  :node="selectedNode"
                  :noClose="true"
                  :showDrillDown="true"
                />
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
                  <TimeSeriesChart
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
              <TagsDashboard
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
              <ClusterComparison
                :clusters="clusters"
                @select-cluster="selectCluster"
              ></ClusterComparison>
            </q-dialog>
            <!-- Node Comparison dialog -->
            <q-dialog
              v-model="showNodeComparison"
              maximized
              transition-show="slide-up"
              transition-hide="slide-down"
            >
              <NodeComparison
                :nodes="selectedCluster?.nodes || nodes"
                @select-node="selectNode"
              ></NodeComparison>
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
import { ref, computed, ComputedRef } from 'vue';
import * as d3 from 'd3';
import D3Graph from 'components/D3Graph.vue';
import JsonFileSelector from 'components/JsonFileSelector.vue';
import MetricHistogram from './MetricHistogram.vue';
import TimeSeriesChart from './TimeSeriesChart.vue';
import TagsDashboard from './TagsDashboard.vue';
import NodeCard from './NodeCard.vue';
import ClusterComparison from './ClusterComparison.vue';
import NodeComparison from './NodeComparison.vue';
import {
  Node,
  Edge,
  GraphData,
  ClusterInfo,
  TagStats,
  AbstractNode,
  HistogramData,
  MetricValue,
} from 'components/models';
import { formatMetricValue } from 'src/helpers/utils';
import {
  aggregateNodesMetrics,
  initClusters,
  sortTags,
} from 'src/helpers/graph';

const d3GraphRef = ref<InstanceType<typeof D3Graph> | null>(null);
const showLoadDataDialog = ref(false);
const dataSourceDescription = ref('');
const nodes = ref([] as Node[]);
const edges = ref([] as Edge[]);
const clusters = ref<ClusterInfo[]>([]);
const selectedCluster = ref(null as ClusterInfo | null);
const selectedNode = ref(null as Node | null);
const activeTab = ref('info');
const showClusterComparison = ref(false);
const showNodeComparison = ref(false);
const showTimeSeriesDialog = ref(false);
const showTagsDashboardDialog = ref(false);
const selectedMetric = ref('');
let clusterForAllNodes: ClusterInfo | undefined;
const tagSearchQuery = ref('');

const sortedTags = computed(() => {
  if (!selectedCluster.value) {
    // Global scope - collect tags from all vertices
    return collectTags(nodes.value);
  }
  return collectTags(selectedCluster.value.nodes);
});
const filteredTags = computed(() => {
  const query = tagSearchQuery.value.toLowerCase().trim();
  if (!query) return sortedTags.value;

  return sortedTags.value.filter((tagInfo) =>
    tagInfo.tag.toLowerCase().includes(query),
  );
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
  showLoadDataDialog.value = false;
  dataSourceDescription.value = args.origin || 'Custom data';
  const jsonData: GraphData = args.data;
  sortTags(jsonData.nodes);
  clusters.value = initClusters(jsonData.nodes, jsonData.edges);
  nodes.value = jsonData.nodes;
  edges.value = jsonData.edges;
  clusterForAllNodes = {
    id: '',
    nodes: nodes.value,
    description: 'All nodes',
    metrics: aggregateNodesMetrics(nodes.value),
  };
  selectedCluster.value = clusterForAllNodes;
  selectedNode.value = null;
  history.setRoot(clusterForAllNodes);
}

interface BreadcrumbBase {
  description: string;
  onClick: () => void;
}

interface RegularBreadcrumb extends BreadcrumbBase {
  isDropdown: false;
}

interface DropdownBreadcrumb extends BreadcrumbBase {
  isDropdown: true;
  items: BreadcrumbBase[];
}

type BreadcrumbItem = RegularBreadcrumb | DropdownBreadcrumb;

class ContextHistory {
  private _history = ref<Array<{ cluster: ClusterInfo; isRoot: boolean }>>([]);

  setRoot(root: ClusterInfo) {
    this._history.value = [{ cluster: root, isRoot: true }];
  }

  clear() {
    this._history.value = [];
  }

  reset() {
    d3GraphRef.value?.selectNodes([]);
  }

  onReset() {
    while (this._history.value.length !== 1) {
      this._history.value.pop();
    }
    selectedCluster.value = this._history.value[0].cluster;
    selectedNode.value = null;
  }

  onPush(cluster: ClusterInfo) {
    this._history.value.push({ cluster, isRoot: false });
    selectedCluster.value = cluster;
  }

  onPop() {
    if (this._history.value.length > 1) {
      this._history.value.pop();
      selectedCluster.value =
        this._history.value[this._history.value.length - 1].cluster;
    }
  }

  private _activate(historyItem: { cluster: ClusterInfo; isRoot: boolean }) {
    // Find the index of the clicked item
    const index = this._history.value.findIndex(
      (item) => item.cluster === historyItem.cluster,
    );

    if (index === -1) return;

    // Remove all items after this index
    while (this._history.value.length > index) {
      this._history.value.pop();
    }

    // Trigger graph selection
    if (historyItem.cluster.id) {
      d3GraphRef.value?.setCurrentCluster(historyItem.cluster.id);
    } else {
      d3GraphRef.value?.selectNodes(
        historyItem.cluster.nodes,
        historyItem.cluster.description,
      );
    }
  }

  get breadcrumbs(): ComputedRef<BreadcrumbItem[]> {
    return computed<BreadcrumbItem[]>(() => {
      const history = this._history.value;
      if (history.length <= 2) {
        // If only root or root + one item, show all
        return history.map((item) => ({
          description: this.getDescription(item.cluster),
          onClick: () => (item.isRoot ? this.reset() : this._activate(item)),
          isDropdown: false as const,
        }));
      }

      // Show root, ellipsis with dropdown, and current
      return [
        // Root item
        {
          description: this.getDescription(history[0].cluster),
          onClick: () => this.reset(),
          isDropdown: false as const,
        },
        // Ellipsis menu with intermediate items
        {
          description: '...',
          onClick: () => {},
          isDropdown: true as const,
          items: history.slice(1, -1).map((item) => ({
            description: this.getDescription(item.cluster),
            onClick: () => this._activate(item),
          })),
        },
        // Current item
        {
          description: this.getDescription(history[history.length - 1].cluster),
          onClick: () => {}, // No-op for last item
          isDropdown: false as const,
        },
      ];
    });
  }

  private getDescription(cluster: ClusterInfo) {
    if (cluster.description) {
      return cluster.description;
    }
    if (cluster.id) {
      return 'Cluster #' + cluster.id;
    }
    return '';
  }
}
const history = new ContextHistory();

function unloadData() {
  nodes.value = [];
  edges.value = [];
  clusters.value = [];
  dataSourceDescription.value = '';
  history.clear();
  selectedCluster.value = null;
  selectedNode.value = null;
}

/**
 * Collect tags from nodes.
 */
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

function selectNodesByTag(tagStat: TagStats) {
  // Use the D3Graph method to highlight these nodes
  d3GraphRef.value?.selectNodes(
    tagStat.nodes,
    `Nodes with tag '${tagStat.tag}''`,
  );
}

/** Handler of clicking on a tag in Tags Dashboard.
 * @param tagStat
 */
function onTagDashboardSelect(tagStat: TagStats) {
  showTagsDashboardDialog.value = false;
  d3GraphRef.value?.selectNodes(
    tagStat.nodes,
    `Nodes with tag '${tagStat.tag}'`,
  );
}

function onNodeSelected(node: Node | null) {
  selectedNode.value = node;
}

function onClusterSelected(cluster: ClusterInfo | null) {
  if (!cluster) {
    history.onReset();
  } else {
    history.onPush(cluster);
  }
}

/** Handler of clicking on a cluster in 'Compare Clusters' dialog. */
function selectCluster(clusterId: string) {
  showClusterComparison.value = false;
  d3GraphRef.value?.setCurrentCluster(clusterId);
}

/** Handler of clicking on a node in 'Compare Nodes' dialog. */
function selectNode(nodeId: number) {
  showNodeComparison.value = false;
  const node = nodes.value.find((n) => n.id === nodeId);
  if (node) {
    d3GraphRef.value?.selectNodes([node]);
    // NOTE: selectNodes won't trigger 'select-node' event
    selectedNode.value = node;
  }
}

function getHistogramData(metric: string) {
  if (selectedCluster.value) {
    return createHistogramData(selectedCluster.value.nodes, metric);
  }
  return [];
}

const getClusterSizesHistogramData = computed(() => {
  const clusterSizeNodes = clusters.value.map((cluster) => ({
    info: { clusterSize: cluster.nodes.length },
    id: cluster.id.toString(),
  }));

  return createHistogramData(clusterSizeNodes, 'clusterSize');
});

function createHistogramData(
  nodes: AbstractNode[],
  metric: string,
): HistogramData[] {
  if (!nodes || nodes.length === 0) return [];

  // Get all values of the metric
  const values = nodes
    .map((node) => ({ value: node.info?.[metric] as MetricValue, node }))
    .filter((v) => v.value !== undefined && v.value !== null);

  if (!values || values.length === 0) return [];
  // Check if the values are strings
  const isStringData = typeof values[0].value === 'string';

  if (isStringData) {
    // Count frequencies of each unique value
    const frequencies = d3.rollup(
      values,
      (v) => v.length,
      (d) => d.value,
    );

    // Convert to array and sort by frequency
    const sortedData = Array.from(frequencies, ([value, count]) => ({
      value,
      count,
      nodes: values.filter((v) => v.value === value).map((v) => v.node),
    }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // Limit to top 10

    // Convert to HistogramData format
    return sortedData.map((d) => ({
      x0: d.value as string,
      count: d.count,
      nodes: d.nodes,
    }));
  } else {
    // Create bin generator
    const binner = d3
      .bin<{ value: MetricValue; node: AbstractNode }, number>()
      .value((d) => d.value as number)
      .domain([
        d3.min(values, (d) => d.value as number)!,
        d3.max(values, (d) => d.value as number)!,
      ])
      .thresholds(10); // number of bins

    // Generate bins
    const bins = binner(values);

    return bins.map((bin) => ({
      x0: bin.x0 || 0,
      x1: bin.x1 || 0,
      count: bin.length,
      nodes: bin.map((d) => d.node),
    }));
  }
}

/**
 * Handle of click on a metric's histogram.
 * Clicking on a bar selects nodes having the metric's value range.
 */
function onClusterHistogramMetricClicked(args: {
  metric: string;
  nodes: AbstractNode[];
  scalar: boolean;
  range: number[] | string[];
}) {
  if (d3GraphRef.value) {
    const msg = args.scalar
      ? `Nodes with '${args.metric}' metric equals to '${args.range[0]}'`
      : `Nodes with '${args.metric}' metric values in [${args.range[0]}, ${args.range[1]}] range`;
    if (args.metric === 'Cluster Size' && args.nodes?.length) {
      // special case - nodes are actually clusters
      const nodes = args.nodes.flatMap((n) =>
        clusters.value.filter((c) => c.id === n.id).flatMap((c) => c.nodes),
      );
      d3GraphRef.value.selectNodes(nodes, msg);
    } else {
      d3GraphRef.value.selectNodes(args.nodes as Node[], msg);
    }
  }
}

function doShowTimeSeriesDialog(metric: string) {
  selectedMetric.value = metric;
  showTimeSeriesDialog.value = true;
}
</script>

<style scoped>
.main-component {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Prevent main component from scrolling */
}

.controls-bar {
  flex: 0 0 auto; /* Don't allow controls to grow/shrink */
}

.content-area {
  flex: 1;
  min-height: 0; /* Allow content to shrink */
  overflow: hidden; /* Prevent content area from causing scroll */
}

.graph-container {
  height: 100%;
  overflow: hidden;
}

.graph-area {
  height: 100%;
  width: 100%;
}

.side-menu-container {
  height: 100%;
}

.side-menu {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* Only allow scrolling in the menu card */
}

/* Make tab panels scrollable while keeping tabs fixed */
:deep(.q-tab-panels) {
  overflow-y: auto;
}

.text-h6 {
  margin-bottom: 16px;
}
</style>
