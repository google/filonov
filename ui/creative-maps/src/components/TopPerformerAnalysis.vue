<template>
  <div class="top-performer-analysis" ref="rootEl">
    <div class="analysis-controls">
      <div class="row q-mb-sm">
        <q-radio
          v-model="analysisMode"
          val="target-percentage"
          label="Find creatives needed for"
          dense
          @update:model-value="updateAnalysis"
        />
        <q-input
          v-if="analysisMode === 'target-percentage'"
          v-model.number="targetPercentage"
          type="number"
          min="1"
          max="99"
          class="q-ml-md"
          dense
          style="width: 60px"
          @update:model-value="updateAnalysis"
        />
        <span v-if="analysisMode === 'target-percentage'" class="q-ml-xs"
          >% of total</span
        >
      </div>
      <div class="row q-mb-sm">
        <q-radio
          v-model="analysisMode"
          val="top-n"
          label="Show top"
          dense
          @update:model-value="updateAnalysis"
        />
        <q-input
          v-if="analysisMode === 'top-n'"
          v-model.number="topN"
          type="number"
          min="1"
          class="q-ml-md"
          dense
          style="width: 60px"
          @update:model-value="updateAnalysis"
        />
        <span v-if="analysisMode === 'top-n'" class="q-ml-xs">creatives</span>
      </div>
    </div>

    <div v-if="result" class="analysis-result q-mt-sm">
      <q-card flat bordered class="result-card">
        <q-card-section v-if="analysisMode === 'target-percentage'">
          <div class="text-subtitle2">
            {{ result.requiredPercentage.toFixed(1) }}% of creatives contribute
            {{ result.contributionPercentage.toFixed(1) }}% of total
            {{ metric }}
          </div>
          <div class="text-caption">
            {{ result.nodeCount }} out of {{ result.totalNodes }} creatives
          </div>
        </q-card-section>
        <q-card-section v-else>
          <div class="text-subtitle2">
            Top {{ result.nodeCount }} creatives contribute
            {{ result.contributionPercentage.toFixed(1) }}% of total
            {{ metric }}
          </div>
          <div class="text-caption">
            {{ result.nodeCount }} out of {{ result.totalNodes }} creatives ({{
              result.requiredPercentage.toFixed(1)
            }}%)
          </div>
        </q-card-section>
        <q-card-section class="q-pa-sm">
          <svg ref="svgRef" width="100%" :height="chartHeight"></svg>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn
            flat
            dense
            color="primary"
            label="Select these creatives"
            @click="selectTopPerformers"
          />
        </q-card-actions>
      </q-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import * as d3 from 'd3';
import { AbstractNode, ClusterInfo } from './models';

interface Props {
  data: ClusterInfo;
  metric: string;
  height?: number;
}

const props = withDefaults(defineProps<Props>(), { height: 200 });

const emit = defineEmits<{
  (
    e: 'select-nodes',
    args: {
      nodes: AbstractNode[];
      message: string;
    },
  ): void;
}>();

const rootEl = ref<HTMLElement | null>(null);
const svgRef = ref<SVGSVGElement | null>(null);
const analysisMode = ref<'target-percentage' | 'top-n'>('target-percentage');
const targetPercentage = ref(80);
const topN = ref(10);
const result = ref<TopPerformerAnalysis | null>(null);
const chartHeight = computed(() => Math.min(props.height, 120));

// Update the analysis when props or settings change
watch(
  [() => props.metric, analysisMode, targetPercentage, topN],
  () => {
    updateAnalysis();
  },
  { immediate: true },
);

function updateAnalysis() {
  const targetValue =
    analysisMode.value === 'target-percentage'
      ? targetPercentage.value
      : topN.value;

  result.value = getTopPerformersAnalysis(
    props.data.nodes,
    props.metric,
    analysisMode.value,
    targetValue,
  );

  drawVisualization();
}

/**
 * Creates data for analyzing top performing creatives based on a metric.
 * Supports two modes:
 * 1. Find minimum % of nodes needed to reach a target % of total metric value
 * 2. Show contribution of top N nodes
 *
 * @param nodes - Array of nodes to analyze
 * @param metric - Metric name to use
 * @param mode - 'target-percentage' or 'top-n'
 * @param targetValue - Target percentage (0-100) or number of top nodes
 * @returns Analysis result with visual data
 */
function getTopPerformersAnalysis(
  nodes: AbstractNode[],
  metric: string,
  mode: 'target-percentage' | 'top-n' = 'target-percentage',
  targetValue: number = 80,
): TopPerformerAnalysis {
  if (!nodes || nodes.length === 0) {
    return {
      mode,
      targetValue,
      requiredPercentage: 0,
      contributionPercentage: 0,
      nodeCount: 0,
      totalNodes: 0,
      nodes: [],
      allNodes: [],
      visualData: [],
    };
  }

  // Filter nodes that have the specified metric and the metric is numeric
  const nodesWithMetric = nodes.filter(
    (node) =>
      node.info?.[metric] !== undefined &&
      node.info?.[metric] !== null &&
      typeof node.info?.[metric] === 'number' &&
      (node.info?.[metric] as number) > 0, // Only include positive values
  );

  if (nodesWithMetric.length === 0) {
    return {
      mode,
      targetValue,
      requiredPercentage: 0,
      contributionPercentage: 0,
      nodeCount: 0,
      totalNodes: 0,
      nodes: [],
      allNodes: [],
      visualData: [],
    };
  }

  // Sort nodes by metric value in descending order (highest first)
  const sortedNodes = [...nodesWithMetric].sort(
    (a, b) => (b.info?.[metric] as number) - (a.info?.[metric] as number),
  );

  // Calculate total metric value across all nodes
  const totalMetricValue = sortedNodes.reduce(
    (sum, node) => sum + (node.info?.[metric] as number),
    0,
  );

  // Initialize result
  let resultNodes: AbstractNode[] = [];
  let requiredPercentage = 0;
  let contributionPercentage = 0;

  if (mode === 'target-percentage') {
    // Find minimum percentage of nodes needed to reach target percentage of total value
    const targetMetricValue = (targetValue / 100) * totalMetricValue;
    let accumulatedValue = 0;

    for (let i = 0; i < sortedNodes.length; i++) {
      accumulatedValue += sortedNodes[i].info?.[metric] as number;
      resultNodes.push(sortedNodes[i]);

      if (accumulatedValue >= targetMetricValue) {
        requiredPercentage = ((i + 1) / sortedNodes.length) * 100;
        contributionPercentage = (accumulatedValue / totalMetricValue) * 100;
        break;
      }
    }
  } else {
    // top-n mode
    // Get contribution of top N nodes
    const numNodes = Math.min(targetValue, sortedNodes.length);
    resultNodes = sortedNodes.slice(0, numNodes);

    const contributionValue = resultNodes.reduce(
      (sum, node) => sum + (node.info?.[metric] as number),
      0,
    );

    requiredPercentage = (numNodes / sortedNodes.length) * 100;
    contributionPercentage = (contributionValue / totalMetricValue) * 100;
  }

  // Create visualization data (for both the selected nodes and the rest)
  const visualData: ParetoVisualizationData[] = [];

  // Top performers bucket
  visualData.push({
    label:
      mode === 'target-percentage'
        ? `Top ${requiredPercentage.toFixed(1)}%`
        : `Top ${resultNodes.length}`,
    nodePercentage: requiredPercentage,
    valuePercentage: contributionPercentage,
    nodes: resultNodes,
    isHighlighted: true,
  });

  // Remaining nodes bucket (if any)
  if (resultNodes.length < sortedNodes.length) {
    const remainingNodes = sortedNodes.slice(resultNodes.length);
    remainingNodes.reduce(
      (sum, node) => sum + (node.info?.[metric] as number),
      0,
    );

    visualData.push({
      label:
        mode === 'target-percentage'
          ? `Bottom ${(100 - requiredPercentage).toFixed(1)}%`
          : `Remaining ${sortedNodes.length - resultNodes.length}`,
      nodePercentage: 100 - requiredPercentage,
      valuePercentage: 100 - contributionPercentage,
      nodes: remainingNodes,
      isHighlighted: false,
    });
  }

  return {
    mode,
    targetValue,
    requiredPercentage,
    contributionPercentage,
    nodeCount: resultNodes.length,
    totalNodes: sortedNodes.length,
    nodes: resultNodes,
    allNodes: sortedNodes,
    visualData,
  };
}

/**
 * Interface for Pareto visualization data
 */
interface ParetoVisualizationData {
  label: string; // Label for the data point
  nodePercentage: number; // % of total nodes in this bucket
  valuePercentage: number; // % of total value contributed by this bucket
  nodes: AbstractNode[]; // Array of nodes in this bucket
  isHighlighted: boolean; // Whether this is the highlighted part (e.g., top performers)
}

/**
 * Interface for top performer analysis result
 */
interface TopPerformerAnalysis {
  mode: 'target-percentage' | 'top-n'; // Analysis mode
  targetValue: number; // Target value used for analysis
  requiredPercentage: number; // % of nodes required to reach target
  contributionPercentage: number; // % of total value contributed by these nodes
  nodeCount: number; // Number of nodes in the result
  totalNodes: number; // Total number of nodes analyzed
  nodes: AbstractNode[]; // Nodes that meet the criteria
  allNodes: AbstractNode[]; // All nodes that were analyzed
  visualData: ParetoVisualizationData[]; // Data for visualization
}

function drawVisualization() {
  if (!svgRef.value || !result.value) return;

  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove();

  const margin = { top: 10, right: 10, bottom: 10, left: 10 };
  const width = svgRef.value.clientWidth;
  const height = chartHeight.value;
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Create a horizontal stacked bar chart
  const x = d3.scaleLinear().domain([0, 100]).range([0, innerWidth]);

  // Create the segments
  g.selectAll('rect')
    .data(result.value.visualData)
    .join('rect')
    .attr('x', (d, i) =>
      i === 0
        ? 0
        : x(
            result
              .value!.visualData.slice(0, i)
              .reduce((sum, item) => sum + item.nodePercentage, 0),
          ),
    )
    .attr('y', innerHeight / 4)
    .attr('width', (d) => x(d.nodePercentage))
    .attr('height', innerHeight / 2)
    .attr('fill', (d) => (d.isHighlighted ? '#2171b5' : '#deebf7'))
    .attr('stroke', '#fff')
    .attr('stroke-width', 1);

  // Add percentage labels
  g.selectAll('.node-percent')
    .data(result.value.visualData)
    .join('text')
    .attr('class', 'node-percent')
    .attr('x', (d, i) =>
      i === 0
        ? x(d.nodePercentage / 2)
        : x(
            result
              .value!.visualData.slice(0, i)
              .reduce((sum, item) => sum + item.nodePercentage, 0) +
              d.nodePercentage / 2,
          ),
    )
    .attr('y', innerHeight / 4 - 5)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', (d) => (d.isHighlighted ? '#2171b5' : '#666'))
    .text((d) => `${d.nodePercentage.toFixed(1)}%`);

  // Add value percentage labels
  g.selectAll('.value-percent')
    .data(result.value.visualData)
    .join('text')
    .attr('class', 'value-percent')
    .attr('x', (d, i) =>
      i === 0
        ? x(d.nodePercentage / 2)
        : x(
            result
              .value!.visualData.slice(0, i)
              .reduce((sum, item) => sum + item.nodePercentage, 0) +
              d.nodePercentage / 2,
          ),
    )
    .attr('y', (innerHeight * 3) / 4 + 15)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', (d) => (d.isHighlighted ? '#2171b5' : '#666'))
    .text((d) => `${d.valuePercentage.toFixed(1)}%`);

  // Add segment labels
  g.selectAll('.segment-label')
    .data(result.value.visualData)
    .join('text')
    .attr('class', 'segment-label')
    .attr('x', (d, i) =>
      i === 0
        ? x(d.nodePercentage / 2)
        : x(
            result
              .value!.visualData.slice(0, i)
              .reduce((sum, item) => sum + item.nodePercentage, 0) +
              d.nodePercentage / 2,
          ),
    )
    .attr('y', innerHeight / 2 + 5)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', (d) => (d.isHighlighted ? 'white' : '#333'))
    .text((d) => d.label);
}

function selectTopPerformers() {
  if (!result.value) return;

  const topPerformers = result.value.nodes;
  const message =
    analysisMode.value === 'target-percentage'
      ? `Top ${result.value.requiredPercentage.toFixed(1)}% of creatives contributing ${result.value.contributionPercentage.toFixed(1)}% of ${props.metric}`
      : `Top ${result.value.nodeCount} creatives contributing ${result.value.contributionPercentage.toFixed(1)}% of ${props.metric}`;

  emit('select-nodes', {
    nodes: topPerformers,
    message,
  });
}
</script>

<style scoped>
.top-performer-analysis {
  width: 100%;
  margin: 10px 0;
}
.analysis-controls {
  display: flex;
  flex-direction: column;
}
.result-card {
  width: 100%;
}
</style>
