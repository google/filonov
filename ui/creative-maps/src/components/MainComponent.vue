<template>
  <div class="main-component q-pa-md">
    <div class="row items-center q-pa-sm controls-bar" :class="$q.dark.isActive ? 'bg-grey-9' : 'bg-grey-2'">
      <q-btn
        class="q-mr-md"
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
          <br />
          {{ dataSourceAuxInfo }}
        </template>
        <span v-else class="text-grey">No data loaded</span>
      </div>
      <q-btn v-if="nodes.length" @click="unloadData" class="q-ml-md"
        >Unload</q-btn
      >
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
                <q-item-label>Creative count</q-item-label>
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
              <q-tab v-if="selectedNode" name="node" label="Creative" />
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
                      <div class="text-subtitle2">Total Creatives</div>
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
                      label="Compare Creatives"
                      icon="compare_arrows"
                      class="q-mt-md"
                      @click="showNodeComparison = true"
                      style="width: 100%"
                    />
                  </div>
                </div>
              </q-tab-panel>

              <q-tab-panel name="metrics">
                <div class="row items-center q-mb-md">
                  <q-btn-toggle
                    v-model="visualizationMode"
                    flat
                    dense
                    toggle-color="primary"
                    class="toggle-with-underline"
                    :options="[
                      {
                        label: 'Distribution',
                        value: 'histogram',
                        slot: 'histogram-tooltip',
                      },
                      {
                        label: 'Pareto',
                        value: 'pareto',
                        slot: 'pareto-tooltip',
                      },
                      {
                        label: 'Top Performers',
                        value: 'top-performers',
                        slot: 'top-tooltip',
                      },
                    ]"
                  >
                    <template v-slot:histogram-tooltip>
                      <q-tooltip
                        >Shows how many creatives fall into each value
                        range</q-tooltip
                      >
                    </template>
                    <template v-slot:pareto-tooltip>
                      <q-tooltip
                        >Shows accumulated contribution by percentile
                        groups</q-tooltip
                      >
                    </template>
                    <template v-slot:top-tooltip>
                      <q-tooltip
                        >Find minimal set of creatives that contribute the
                        most</q-tooltip
                      >
                    </template>
                  </q-btn-toggle>
                </div>
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
                      <!-- Distribution Histogram -->
                      <MetricHistogram
                        v-if="visualizationMode === 'histogram'"
                        :data="getHistogramData(metric.toString())"
                        :metric="metric.toString()"
                        @metric-clicked="onClusterHistogramMetricClicked"
                      />
                      <!-- Pareto Chart -->
                      <MetricHistogram
                        v-else-if="visualizationMode === 'pareto'"
                        :data="getParetoHistogramData(metric.toString())"
                        :is-pareto-mode="true"
                        :metric="metric.toString()"
                        @metric-clicked="onParetoHistogramMetricClicked"
                      />
                      <!-- Top performers analysis view -->
                      <TopPerformerAnalysis
                        v-else
                        :data="selectedCluster"
                        :metric="metric.toString()"
                        @select-nodes="onSelectTopPerformers"
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
                        {{ tagInfo.avgScore.toFixed(2) }} ({{ tagInfo.freq }})
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
                @select-nodes="selectNodes"
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
        <q-card-section class="row items-center q-py-md">
          <div class="text-h6 q-ml-sm">Load Graph Data</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-none">
          <json-file-selector @json-loaded="onDataLoaded" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, ComputedRef } from 'vue';
import { useQuasar } from 'quasar';
import * as d3 from 'd3';
import D3Graph from 'components/D3Graph.vue';
import JsonFileSelector from 'components/JsonFileSelector.vue';
import MetricHistogram from './MetricHistogram.vue';
import TopPerformerAnalysis from './TopPerformerAnalysis.vue';
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
  ParetoHistogramData,
} from 'components/models';
import {
  aggregateNodesMetrics,
  initClusters,
  optimizeGraphEdges,
  sortTags,
  formatMetricValue,
} from 'src/helpers/graph';

const $q = useQuasar();
const d3GraphRef = ref<InstanceType<typeof D3Graph> | null>(null);
const showLoadDataDialog = ref(false);
const dataSourceDescription = ref(''); // description of data file (name/path)
const dataSourceAuxInfo = ref(''); // additional info about loaded data
const nodes = ref([] as Node[]);
const edges = ref([] as Edge[]);
const clusters = ref<ClusterInfo[]>([]);
const selectedCluster = ref(null as ClusterInfo | null);
const selectedNode = ref(null as Node | null);
const activeTab = ref('info');
const visualizationMode = ref('histogram');
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

async function onDataLoaded(args: {
  data: GraphData;
  origin: string;
  optimizeGraph: boolean;
  threshold?: number;
}) {
  showLoadDataDialog.value = false;
  dataSourceDescription.value = args.origin || 'Custom data';
  const graphData: GraphData = args.data;
  if (args.data.graph?.period) {
    dataSourceAuxInfo.value = `period: ${args.data.graph?.period.start_date} - ${args.data.graph?.period.end_date}`;
  }
  sortTags(graphData.nodes);
  console.log('threshold: ' + args.threshold);
  if (args.threshold !== undefined && args.threshold > 0) {
    // filter edges by threshold
    const threshold = args.threshold;
    const edges = graphData.edges.filter((e) => e.similarity > threshold);
    console.log(
      `Graph optimized: edges originally ${graphData.edges.length} filtered by similarity threshold ${threshold} to ${edges.length}`,
    );
    graphData.edges = edges;
  }
  clusters.value = initClusters(graphData.nodes, graphData.edges, 'cost');
  // optimize edges within each cluster
  if (args.optimizeGraph) {
    const optimizedEdges = optimizeGraphEdges(
      graphData.nodes,
      graphData.edges,
      0,
    );
    console.log(
      `Graph has been optimized: originally ${graphData.edges.length} edges optimized to ${optimizedEdges.length}`,
    );
    edges.value = optimizedEdges;
  } else {
    edges.value = graphData.edges;
  }
  nodes.value = graphData.nodes;
  clusterForAllNodes = {
    id: '',
    nodes: nodes.value,
    description: 'All creatives',
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
    if (cluster.id === 'manual-selection') {
      // for manual selection we won't add history
      if (
        this._history.value[this._history.value.length - 1].cluster.id ===
        'manual-selection'
      ) {
        selectedCluster.value = cluster;
        return;
      }
    }
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
  const tagsMap = new Map<
    string,
    { freq: number; avgScore: number; nodes: Node[] }
  >();

  nodes.forEach((node: Node) => {
    node.tags?.forEach((tagInfo) => {
      if (!tagsMap.has(tagInfo.tag)) {
        tagsMap.set(tagInfo.tag, { freq: 0, nodes: [], avgScore: 0 });
      }
      const stats = tagsMap.get(tagInfo.tag)!;
      stats.freq += 1;
      stats.avgScore += tagInfo.score;
      stats.nodes.push(node);
    });
  });

  return Array.from(tagsMap.entries())
    .map(([tag, stats]) => ({
      tag,
      freq: stats.freq,
      avgScore: stats.avgScore / stats.nodes.length,
      nodes: stats.nodes,
    }))
    .sort((a, b) => b.avgScore - a.avgScore); // Sort by svg. score descending
}

function selectNodesByTag(tagStat: TagStats) {
  // Use the D3Graph method to highlight these nodes
  d3GraphRef.value?.selectNodes(
    tagStat.nodes,
    `Creatives with tag '${tagStat.tag}''`,
  );
}

/** Handler of clicking on a tag in Tags Dashboard.
 * @param tagStat
 */
function onTagDashboardSelect(tagStat: TagStats) {
  showTagsDashboardDialog.value = false;
  d3GraphRef.value?.selectNodes(
    tagStat.nodes,
    `Creatives with tag '${tagStat.tag}'`,
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

/** Handler of clicking on a node in 'Compare Creatives' dialog. */
function selectNode(nodeId: number) {
  showNodeComparison.value = false;
  const node = nodes.value.find((n) => n.id === nodeId);
  if (node) {
    d3GraphRef.value?.selectNodes([node]);
    // NOTE: selectNodes won't trigger 'select-node' event
    selectedNode.value = node;
  }
}

/** Handler of clicking on 'View Nodes' for a tag in 'Tags Dashboard' dialog. */
function selectNodes(nodes: Node[]) {
  showTagsDashboardDialog.value = false;
  d3GraphRef.value?.selectNodes(nodes);
}

function getHistogramData(metric: string) {
  if (selectedCluster.value) {
    return createHistogramData(selectedCluster.value.nodes, metric);
  }
  return [];
}

function getParetoHistogramData(metric: string) {
  if (selectedCluster.value) {
    return createParetoHistogramData(selectedCluster.value.nodes, metric);
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
 * Creates data for a Pareto-style histogram showing accumulated metric contribution.
 * Shows what percentage of nodes contributes to what percentage of the total metric value.
 * @param nodes - Array of nodes to analyze
 * @param metric - Metric name to use
 * @param numBuckets - Number of buckets to create (default: 5)
 * @returns Array of ParetoHistogramData objects
 */
function createParetoHistogramData(
  nodes: AbstractNode[],
  metric: string,
  numBuckets: number = 10,
): ParetoHistogramData[] {
  if (!nodes || nodes.length === 0) return [];

  // Filter nodes that have the specified metric and the metric is numeric
  const nodesWithMetric = nodes.filter(
    (node) =>
      node.info?.[metric] !== undefined &&
      node.info?.[metric] !== null &&
      typeof node.info?.[metric] === 'number',
  );

  if (nodesWithMetric.length === 0) return [];

  // Sort nodes by metric value in descending order (highest first)
  const sortedNodes = [...nodesWithMetric].sort(
    (a, b) => (b.info?.[metric] as number) - (a.info?.[metric] as number),
  );

  // Calculate total metric value across all nodes
  const totalMetricValue = sortedNodes.reduce(
    (sum, node) => sum + (node.info?.[metric] as number),
    0,
  );

  // Create buckets based on percentage of nodes
  const result: ParetoHistogramData[] = [];
  const nodesPerBucket = Math.ceil(sortedNodes.length / numBuckets);

  let accumulatedValue = 0;
  let accumulatedNodes: AbstractNode[] = [];

  for (let i = 0; i < numBuckets; i++) {
    const startIdx = i * nodesPerBucket;
    const endIdx = Math.min((i + 1) * nodesPerBucket, sortedNodes.length);

    if (startIdx >= sortedNodes.length) break;

    const bucketNodes = sortedNodes.slice(startIdx, endIdx);
    const bucketValue = bucketNodes.reduce(
      (sum, node) => sum + (node.info?.[metric] as number),
      0,
    );

    accumulatedValue += bucketValue;
    accumulatedNodes = accumulatedNodes.slice(0);
    accumulatedNodes.push(...bucketNodes);

    result.push({
      nodePercentage: (accumulatedNodes.length / sortedNodes.length) * 100,
      valuePercentage: (accumulatedValue / totalMetricValue) * 100,
      bucketValue,
      accumulatedValue,
      nodes: accumulatedNodes,
      label: `Top ${Math.round((accumulatedNodes.length / sortedNodes.length) * 100)}%`,
    });
  }

  return result;
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
      ? `Creatives with '${args.metric}' metric equals to '${args.range[0]}'`
      : `Creatives with '${args.metric}' metric values in [${args.range[0]}, ${args.range[1]}] range`;
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

/**
 * Handling Pareto histogram click
 */
function onParetoHistogramMetricClicked(args: {
  metric: string;
  nodes: AbstractNode[];
  scalar: boolean;
  range: string[] | number[];
}) {
  if (d3GraphRef.value) {
    const msg = `Top performers for '${args.metric}': ${args.range[0]} (${args.nodes.length}) of creatives contribute ${args.range[1]} of total value`;
    d3GraphRef.value.selectNodes(args.nodes as Node[], msg);
  }
}
function onSelectTopPerformers(args: {
  nodes: AbstractNode[];
  message: string;
}) {
  if (d3GraphRef.value) {
    d3GraphRef.value.selectNodes(args.nodes as Node[], args.message);
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

.toggle-with-underline .q-btn[aria-pressed='true'] {
  border-bottom: 2px solid var(--q-primary);
  font-weight: bold;
}
</style>
