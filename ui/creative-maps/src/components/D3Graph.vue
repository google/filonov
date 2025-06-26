<template>
  <div class="d3-graph">
    <div class="graph-controls">
      <q-toggle v-model="showLabels" label="Show Labels" color="primary" />
      <q-toggle
        v-model="showImages"
        label="Show Node Preview"
        color="primary"
      />
      <q-toggle v-model="physicsActive" label="Physics" color="primary" />
      <q-slider
        v-model="nodeSizeMultiplier"
        :min="0.5"
        :max="5"
        :step="0.1"
        label
        label-always
        color="primary"
        class="q-mx-md"
        style="width: 200px"
      >
        <template v-slot:marker-label-group>
          {{ nodeSizeMultiplier }}x
        </template>
      </q-slider>
      <q-btn
        flat
        dense
        round
        icon="route"
        @click="relayoutGraph"
        color="primary"
      />
      <q-btn
        flat
        dense
        round
        icon="fit_screen"
        @click="fitGraph"
        color="primary"
      />
      <q-btn flat dense round icon="zoom_in" @click="zoomIn" color="primary" />
      <q-btn
        flat
        dense
        round
        icon="zoom_out"
        @click="zoomOut"
        color="primary"
      />
      <q-btn flat dense round icon="search" @click="openSearch" color="primary">
        <q-tooltip>Search (⌘K)</q-tooltip>
      </q-btn>

      <NodeSearchDialog
        ref="searchDialog"
        :nodes="props.nodes"
        @node-selected="handleSearchNodeSelect"
      />
      <div class="row">
        <q-select
          class="col-2 q-mx-md"
          style="max-width: 300px"
          v-model="selectedClusterId"
          :options="clusterIds"
          label="Select Cluster"
          emit-value
          outlined
          map-options
          @update:model-value="setCurrentCluster"
          clearable
        />
        <q-select
          class="col-2"
          style="max-width: 300px"
          v-model="selectedSizeField"
          :options="metricNames"
          label="Select metric for size"
          @update:model-value="setSizeField"
          emit-value
          outlined
          map-options
          clearable
        />
        <q-select
          class="col-2 q-mx-md"
          style="max-width: 300px"
          v-model="layoutStrategy"
          :options="layoutOptions"
          label="Layout Strategy"
          emit-value
          outlined
          map-options
          @update:model-value="changeLayoutStrategy"
        />
      </div>
    </div>
    <div ref="chartContainer" class="graph-content"></div>
    <q-tooltip
      v-model="tooltipVisible"
      :target="tooltipTarget"
      anchor="bottom middle"
      self="top middle"
      :offset="[0, 10]"
      v-if="highlightedNode"
    >
      <div class="text-body2">
        <div class="q-mb-xs">Name: {{ highlightedNode.label }}</div>
        <div class="text-weight-bold q-mb-sm">Metrics:</div>
        <div
          v-for="(value, metric) in highlightedNode.info"
          :key="metric"
          class="q-mb-xs"
        >
          {{ formatMetricName(metric) }}: {{ formatMetricValue(value, metric) }}
        </div>
        <div
          v-if="highlightedNode.tags?.length"
          class="text-weight-bold q-mb-sm"
        >
          Tags (up to top 5 of {{ highlightedNode.tags.length }}):
        </div>
        <div
          class="q-mb-xs"
          v-for="(tag, idx) of highlightedNode.tags?.slice(0, 5)"
          :key="tag.tag"
        >
          {{ idx + 1 }}. {{ tag.tag }} ({{ tag.score.toFixed(3) }})
        </div>
      </div>
    </q-tooltip>
    <q-tooltip
      v-model="edgeTooltipVisible"
      :target="edgeTooltipTarget"
      anchor="bottom middle"
      self="top middle"
      :offset="[0, 10]"
      v-if="highlightedEdge"
    >
      <div class="text-body2">
        <div class="text-weight-bold">
          Similarity: {{ (highlightedEdge?.similarity || 0).toFixed(3) }}
        </div>
      </div>
    </q-tooltip>
    <q-dialog v-model="imageLoading.inProgress" persistent>
      <q-card class="bg-white" style="width: 300px">
        <q-card-section class="row items-center">
          <span class="text-h6">Loading Graph</span>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <div class="text-center q-mb-md">
            Loading node previews: {{ imageLoading.current }} /
            {{ imageLoading.total }}
          </div>
          <q-linear-progress
            :value="imageLoading.current / imageLoading.total"
            color="primary"
            class="q-mt-sm"
          />
        </q-card-section>

        <q-card-section class="row justify-center">
          <q-spinner-dots color="primary" size="40px" />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue';
import * as d3 from 'd3';
import { ClusterInfo, Edge, Node } from 'components/models';
import { aggregateNodesMetrics, formatMetricValue } from 'src/helpers/graph';
import NodeSearchDialog from './NodeSearchDialog.vue';
import { Simulation } from 'd3-force';
import { D3DragEvent, drag } from 'd3-drag';
import { zoom, ZoomBehavior, zoomIdentity, zoomTransform } from 'd3-zoom';
import { Transition } from 'd3-transition';
import { Selection } from 'd3-selection';
import {
  useForceLayout,
  D3Node,
  D3Edge,
  ForceLayoutStrategy,
} from 'src/composables/useForceLayout';

type SVGSelection = Selection<SVGSVGElement, unknown, null, undefined>;
type SVGTransition = Transition<SVGSVGElement, unknown, null, undefined>;
type DragEvent = D3DragEvent<SVGGElement, D3Node, D3Node>;

interface Props {
  nodes: Node[];
  edges: Edge[];
  clusters: ClusterInfo[];
  debug?: boolean;
  labelField?: string;
  sizeField?: string;
}
const props = withDefaults(defineProps<Props>(), { labelField: 'label' });

const emit = defineEmits<{
  (e: 'node-selected', node: Node | null): void;
  (e: 'cluster-selected', cluster: ClusterInfo | null): void;
}>();

const chartContainer = ref<HTMLElement | null>(null);
const tooltipVisible = ref(false);
const tooltipTarget = ref<HTMLElement | undefined>(undefined);
const edgeTooltipVisible = ref(false);
const edgeTooltipTarget = ref<HTMLElement | undefined>(undefined);
const physicsActive = ref(true);
const simulation = ref<Simulation<D3Node, D3Edge> | null>(null);
const zoomBehavior = ref<ZoomBehavior<SVGSVGElement, unknown> | null>(null);
const showLabels = ref(false);
const showImages = ref(true);
const nodeSizeMultiplier = ref(1);
const clusterIds = ref<string[]>([]);
const selectedClusterId = ref<string | null>(null);
const currentNode = ref<Node | null>(null);
const highlightedNode = ref<Node | null>(null);
const highlightedEdge = ref<Edge | null>(null);
const currentCluster = ref<ClusterInfo | null>(null);
const selectedSizeField = ref<string | null | undefined>(props.sizeField);
const searchDialog = ref<InstanceType<typeof NodeSearchDialog> | null>(null);
const isMultiSelectKeyPressed = ref(false);

// Force layout composable
const {
  initForceLayout,
  destroyForceLayout,
  forceLayoutManager,
  layoutStrategies,
} = useForceLayout();

const layoutStrategy = ref<ForceLayoutStrategy>(layoutStrategies[0]);
const layoutOptions = layoutStrategies.map((s) => {
  return { label: s, value: s };
});

let circleBaseSize: number;
let imageBaseSize: number;

const metricNames = computed(() => {
  let keys = props.nodes?.length
    ? props.nodes[0].info
      ? Object.keys(props.nodes[0].info)
      : []
    : [];
  if (keys.length) {
    keys = keys.filter((name) => Number.isFinite(props.nodes[0].info?.[name]));
  }
  return keys;
});

const imageLoading = ref({
  total: 0,
  current: 0,
  failed: 0,
  inProgress: false,
});
let resizeObserver: ResizeObserver;

const formatMetricName = (metric: string) => {
  return metric
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase());
};

function handleNodeClick(event: Event, node: D3Node) {
  // Stop simulation on click
  if (simulation.value) {
    simulation.value.alpha(0);
    simulation.value.stop();
  }

  tooltipTarget.value = event.currentTarget as HTMLElement;
  tooltipVisible.value = true;

  if (isMultiSelectKeyPressed.value) {
    if (currentCluster.value) {
      // Check if node is already in selection
      const nodeIndex = currentCluster.value.nodes.findIndex(
        (n) => n.id === node.id,
      );
      let updatedNodes: Node[];

      if (nodeIndex !== -1) {
        // Remove node from selection
        updatedNodes = [...currentCluster.value.nodes];
        updatedNodes.splice(nodeIndex, 1);
      } else {
        // Add node to selection
        updatedNodes = [...currentCluster.value.nodes, node];
      }

      // If we have nodes, update the manual selection cluster
      if (updatedNodes.length > 0) {
        currentCluster.value = {
          id: 'manual-selection',
          description: 'Manually Selected Nodes',
          nodes: updatedNodes,
          metrics: aggregateNodesMetrics(updatedNodes),
        };
        highlightNodes(updatedNodes);
      } else {
        // If no nodes left, clear selection
        currentCluster.value = null;
        resetHighlight();
      }
    } else {
      currentCluster.value = {
        id: 'manual-selection',
        description: 'Manually Selected Nodes',
        nodes: [node],
        metrics: aggregateNodesMetrics([node]),
      };
      highlightNodes([node]);
    }

    emit('cluster-selected', currentCluster.value);
  } else {
    if (currentNode.value !== node) {
      currentNode.value = node;
      emit('node-selected', node);
    }
    setCurrentCluster(node.cluster);
  }
}

function getCluster(clusterId: string) {
  return props.clusters.find((c) => c.id === clusterId);
}

function highlightNode(event: Event, d: Node) {
  tooltipTarget.value = event.currentTarget as HTMLElement;
  tooltipVisible.value = true;
  highlightedNode.value = d;
  if (!currentCluster.value) {
    // if there's not selected cluster, highlight the cluster that the node belongs to
    const connectedNodes = getCluster(d.cluster)?.nodes || [];
    highlightNodes(connectedNodes);
  }
  return false;
}

function highlightNodes(nodes: Node[]) {
  if (!nodes.length) {
    resetHighlight();
    return;
  }
  const connectedIds = new Set(nodes.map((n) => n.id.toString()));

  // Highlight nodes
  d3.select(chartContainer.value)
    .selectAll<SVGLineElement, D3Node>('g.node-group')
    .transition()
    .duration(200)
    .style('opacity', (node: D3Node) =>
      connectedIds.has(node.id.toString()) ? 1 : 0.1,
    )
    .each(function () {
      const element = d3.select(this);
      const node = element.datum() as Node;
      const isConnected = connectedIds.has(node.id.toString());
      const isCurrent = node.id === highlightedNode.value?.id;
      if (showImages.value && element.select('image').size() > 0) {
        // For image nodes, ONLY modify the image border
        element
          .select('.node-background')
          .style('fill', 'transparent') // Always keep transparent
          .style('stroke', 'transparent'); // Hide the background circle's stroke

        element
          .select('image')
          .style('stroke', isConnected ? '#ff0000' : '#fff')
          .style('stroke-width', isConnected ? '3px' : '1px')
          .style(
            'filter',
            isCurrent ? 'drop-shadow(0 0 30px rgba(255,0,0,0.8))' : 'none',
          );
      } else {
        // For regular circle nodes, keep the current highlighting
        element
          .select('circle')
          .style('stroke', isConnected ? '#ff0000' : '#fff')
          .style('stroke-width', isConnected ? 3 : 1);
      }
    });

  // Highlight links
  d3.select(chartContainer.value)
    .selectAll<SVGLineElement, D3Edge>('line')
    .transition()
    .duration(200)
    .style('opacity', (link: D3Edge) => {
      const sourceConnected = connectedIds.has(link.from.toString());
      const targetConnected = connectedIds.has(link.to.toString());
      return sourceConnected && targetConnected ? 0.6 : 0.1;
    });
}

// select arbitrary number of nodes, it's similar to selecting a cluster (in setCurrentCluster),
// but nodes can be not connected
function selectNodes(nodes: Node[] | null, description?: string) {
  if (!nodes || !nodes.length) {
    currentCluster.value = null;
    resetHighlight();
  } else {
    currentCluster.value = {
      id: '',
      description,
      nodes: nodes,
      metrics: aggregateNodesMetrics(nodes),
    };
    highlightNodes(nodes);
  }
  emit('cluster-selected', currentCluster.value);
}

function centerOnNode(node: D3Node) {
  if (!chartContainer.value || !zoomBehavior.value) return;

  const svg = d3.select(chartContainer.value).select('svg') as SVGSelection;
  const svgNode = svg.node();
  if (!svgNode) return;

  // Get the current viewport dimensions
  const viewportWidth = chartContainer.value.clientWidth;
  const viewportHeight = chartContainer.value.clientHeight;

  // Get the current transform
  const currentTransform = zoomTransform(svgNode as Element);

  // Calculate the new transform to center on the node
  const scale = currentTransform.k; // Keep the current zoom level
  const x = -node.x! * scale + viewportWidth / 2;
  const y = -node.y! * scale + viewportHeight / 2;

  const newTransform = zoomIdentity.translate(x, y).scale(scale);

  // Apply the transform with a smooth transition
  (svg.transition() as SVGTransition)
    .duration(750)
    .call(zoomBehavior.value!.transform, newTransform);
}

function setCurrentCluster(clusterId: string | null) {
  selectedClusterId.value = clusterId;
  if (!clusterId) {
    if (currentCluster.value === null) {
      return;
    }
    currentCluster.value = null;
    resetHighlight();
  } else {
    const cluster = getCluster(clusterId);
    if (currentCluster.value === cluster) {
      return;
    }
    currentCluster.value = cluster || null;
    highlightNodes(cluster?.nodes || []);
  }
  emit('cluster-selected', currentCluster.value);
}

function resetHighlight() {
  tooltipVisible.value = false;
  highlightedNode.value = null;
  if (currentCluster.value) {
    return;
  }

  d3.select(chartContainer.value)
    .selectAll('g.node-group')
    .transition()
    .duration(200)
    .style('opacity', 1)
    .each(function () {
      const element = d3.select(this);

      if (showImages.value && element.select('image').size() > 0) {
        // Reset image node styles - hide background circle
        element
          .select('.node-background')
          .style('fill', 'transparent')
          .style('stroke', 'transparent');

        element
          .select('image')
          .style('stroke', '#fff')
          .style('stroke-width', '1px')
          .style('filter', 'none');
      } else {
        // Reset circle node styles
        element
          .select('circle')
          .style('stroke', '#fff')
          .style('stroke-width', 1);
      }
    });

  d3.select(chartContainer.value)
    .selectAll('line')
    .transition()
    .duration(200)
    .style('opacity', 0.6);
}

async function preloadImages(nodes: Node[]) {
  const imagesToLoad = nodes.filter((n) => n.image);
  let loadedCount = 0;
  let failedCount = 0;
  imageLoading.value = {
    total: imagesToLoad.length,
    current: 0,
    failed: 0,
    inProgress: true,
  };

  const imagePromises = imagesToLoad.map((node) => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        loadedCount++;
        imageLoading.value.failed = failedCount;
        imageLoading.value.current = loadedCount;
        resolve(node.image);
      };
      img.onerror = () => {
        failedCount++;
        imageLoading.value.failed = failedCount;
        imageLoading.value.current = loadedCount;
        reject(node.image);
      };
      img.src = node.image;
    });
  });

  try {
    const results = await Promise.allSettled(imagePromises);
    const failedResults = results.filter(
      (result) => result.status === 'rejected',
    );

    if (failedResults.length > 0) {
      console.error('Failed to load some images:', failedResults);
    }
    imageLoading.value.inProgress = false;

    return failedResults.length === 0;
  } catch (error) {
    console.error('Unexpected error:', error);
    imageLoading.value.inProgress = false;
    return false;
  }
}

function calculateNodeSizes(nodesCount: number) {
  return {
    circleBaseSize:
      Math.max(1, Math.min(1, 40 - Math.log2(nodesCount))) *
      nodeSizeMultiplier.value,

    imageBaseSize:
      Math.min(8, Math.max(1, 20 - Math.log2(nodesCount))) *
      nodeSizeMultiplier.value,
  };
}

function updateNodeSizes(restartSimulation = false) {
  if (!chartContainer.value) return;

  ({ circleBaseSize, imageBaseSize } = calculateNodeSizes(props.nodes.length));

  d3.select(chartContainer.value)
    .selectAll('g > g')
    .each(function () {
      const element = d3.select(this);
      const d = d3.select(this).datum() as Node;
      if (!d) return;
      if (showImages.value && d?.image) {
        const size = restartSimulation
          ? d.size * imageBaseSize
          : Math.min(30, d.size * imageBaseSize * 1.5);
        element
          .select('.node-background')
          .attr('r', size / 2)
          .transition()
          .duration(300);

        element
          .select('image')
          .transition()
          .duration(300)
          .attr('width', size)
          .attr('height', size)
          .attr('x', -size / 2)
          .attr('y', -size / 2);
      } else {
        element
          .select('circle')
          .transition()
          .duration(300)
          .attr('r', d.size * circleBaseSize);
      }
    });

  // Only restart simulation if requested
  if (restartSimulation && forceLayoutManager.value) {
    forceLayoutManager.value.updateCollisionRadius();
  }
}

function getNodeSize(metricValue: number) {
  return Math.log(metricValue) * Math.log10(metricValue);
}

/**
 * Handled of selecting field to use as node size.
 * @param sizeField field name
 */
function setSizeField(sizeField: string) {
  selectedSizeField.value = sizeField;
  props.nodes.forEach((node: Node) => {
    if (sizeField && node.info) {
      if (node.info[sizeField]) {
        node.size = getNodeSize(Number(node.info[sizeField]));
      } else {
        node.size = 10;
      }
    } else {
      node.size = 10;
    }
    node.size = node.size || 10;
  });
  updateNodeSizes(true);
}

async function drawGraph() {
  if (!chartContainer.value) return;

  // Clean up existing simulation
  destroyForceLayout();

  d3.select(chartContainer.value).selectAll('*').remove();
  clusterIds.value = props.clusters.map((c) => c.id);

  const rect = chartContainer.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  const svg = d3
    .select(chartContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .style('display', 'block');

  svg
    .append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .on('click', () => {
      currentNode.value = null;
      highlightedNode.value = null;
      emit('node-selected', null);
      setCurrentCluster(null);
    });
  const g = svg.append('g');

  if (props.nodes.length === 0) {
    return;
  }

  console.log(
    `rendering graph with ${props.nodes.length} nodes and ${props.edges.length} edges`,
  );

  const sizeField = selectedSizeField.value;
  props.nodes.forEach((node: Node) => {
    if (sizeField && !node.size && node.info) {
      if (node.info[sizeField]) {
        node.size = getNodeSize(Number(node.info[sizeField]));
      }
    }
    node.size = node.size || 10;
  });

  props.edges.forEach((edge: Edge) => {
    (edge as D3Edge).source = edge.from; // D3 will resolve this to the actual node
    (edge as D3Edge).target = edge.to; // D3 will resolve this to the actual node
  });

  // Wait for images to load
  if (showImages.value) {
    console.log('Preloading images');
    const res = await preloadImages(props.nodes);
    console.log('Preloading images competed: ' + res);
  }

  // Separate size calculations for circles and images
  const { circleBaseSize, imageBaseSize } = calculateNodeSizes(
    props.nodes.length,
  );

  console.log('Creating links');
  const edgeWidth = 8;
  const link = g
    .append('g')
    .selectAll<SVGLineElement, D3Edge>('line')
    .data<D3Edge>(props.edges as D3Edge[])
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', edgeWidth)
    .attr('cursor', 'pointer')
    .on('mouseenter', (event: Event, d: Edge) => {
      edgeTooltipTarget.value = event.currentTarget as HTMLElement;
      edgeTooltipVisible.value = true;
      highlightedEdge.value = d;

      // Highlight the hovered edge
      d3.select(event.currentTarget as HTMLElement)
        .transition()
        .duration(200)
        .attr('stroke', '#ff0000')
        .attr('stroke-opacity', 1)
        .attr('stroke-width', edgeWidth + 2);
    })
    .on('mouseleave', (event) => {
      edgeTooltipVisible.value = false;
      highlightedEdge.value = null;

      // Reset edge style
      d3.select(event.currentTarget)
        .transition()
        .duration(200)
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', edgeWidth);
    });

  console.log('Creating nodes');
  const nodeGroup = g
    .append('g')
    .selectAll<SVGAElement, D3Node>('g')
    .data(props.nodes)
    .join('g')
    .attr('class', 'node-group')
    .attr('cursor', 'pointer')
    .style('pointer-events', 'all') // Ensure group receives events
    .call(
      drag<SVGGElement, D3Node>()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded),
    );

  nodeGroup.each(function (d) {
    const element = d3.select(this);
    if (showImages.value && d.image) {
      element.selectAll('circle').remove();

      // Add background circle with initial styles
      const size = d.size * imageBaseSize;
      element
        .selectAll('.node-background')
        .data([d])
        .join('circle')
        .attr('class', 'node-background')
        .attr('r', size / 2)
        .attr('fill', 'transparent')
        .style('stroke', '#fff')
        .style('stroke-width', '1px')
        .style('pointer-events', 'all');

      // Create image with initial styles
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let img = element.select<any>('image');
      if (img.empty()) {
        img = element
          .append('image')
          .attr('xlink:href', d.image)
          .attr('width', size)
          .attr('height', size)
          .attr('x', -size / 2)
          .attr('y', -size / 2)
          .style('opacity', 0.9)
          .style('stroke', '#fff')
          .style('stroke-width', '1px')
          .style('pointer-events', 'none');
      }
    } else {
      element.selectAll('image, .node-background').remove();
      element
        .selectAll('circle')
        .data([d])
        .join('circle')
        .attr('r', d.size * circleBaseSize)
        .attr('fill', (d) => d.color || '#69b3a2')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);
    }
    // Add label directly to the node group
    if (showLabels.value) {
      const { imageBaseSize, circleBaseSize } = calculateNodeSizes(
        props.nodes.length,
      );
      const scaledOffset =
        showImages.value && d.image
          ? (d.size * imageBaseSize) / 2 // Exactly same as in updateNodeSizes
          : d.size * circleBaseSize;
      element
        .append('text')
        .text(
          (props.labelField
            ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (d as Record<string, any>)[props.labelField]
            : '') ||
            d.label ||
            d.name ||
            d.id.toString(),
        )
        .attr('x', scaledOffset + 5)
        .attr('dy', '.35em')
        .attr('class', 'node-label')
        .style('font-size', `${circleBaseSize * 10}px`)
        .style('pointer-events', 'none');
    }
  });

  // Add mouse events to nodeGroup after node creation
  nodeGroup
    .on('mouseenter', (event: Event, d: Node) => {
      highlightNode(event, d);
    })
    .on('mouseleave', () => {
      resetHighlight();
    })
    .on('click', (event: Event, d: Node) => {
      event.preventDefault();
      event.stopPropagation();
      handleNodeClick(event, d);
      return false;
    });

  console.log('Setting up simulation');

  const getCollisionRadius = (d: D3Node) => {
    const baseRadius =
      showImages.value && d.image
        ? (d.size * imageBaseSize) / 2
        : d.size * circleBaseSize;
    return baseRadius * 2;
  };

  // Initialize force layout with the selected strategy
  simulation.value = initForceLayout(
    props.nodes,
    props.edges,
    props.clusters,
    {
      physicsActive,
      width,
      height,
      onTick: () => {
        // Update link positions
        link
          .attr('x1', (d) => (d.source as D3Node).x!)
          .attr('y1', (d) => (d.source as D3Node).y!)
          .attr('x2', (d) => (d.target as D3Node).x!)
          .attr('y2', (d) => (d.target as D3Node).y!);

        // Update node positions
        nodeGroup.attr('transform', (d: D3Node) => `translate(${d.x},${d.y})`);
      },
      getCollisionRadius,
    },
    layoutStrategy.value,
  );

  if (forceLayoutManager.value) {
    forceLayoutManager.value.updateCollisionRadius();
  }

  // Set up zoom behavior
  zoomBehavior.value = zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.001, 10])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });

  svg.call(zoomBehavior.value);

  // Optional: fit graph after initial layout
  setTimeout(() => {
    fitGraph();
  }, 1000);

  console.log('drawGraph completed');
}

function changeLayoutStrategy(strategy: ForceLayoutStrategy) {
  layoutStrategy.value = strategy;
  drawGraph(); // Redraw with new strategy
}

function dragStarted(event: DragEvent, d: D3Node) {
  if (!event.active) {
    tooltipVisible.value = false;
    if (
      currentCluster.value &&
      currentCluster.value.nodes.find((n) => n.id === d.id)
    ) {
      // For cluster drag
      simulation.value?.alphaTarget(0.3).restart();

      currentCluster.value.nodes.forEach((node) => {
        const n = simulation.value?.nodes().find((n) => n.id === node.id) as
          | D3Node
          | undefined;
        if (n && n !== d) {
          n.relativeX = n.x! - d.x!;
          n.relativeY = n.y! - d.y!;
          n.fx = n.x;
          n.fy = n.y;
        }
      });
    } else {
      // For single node - gentle forces
      simulation.value
        ?.alphaTarget(0.1)
        .velocityDecay(0.7)
        .alpha(0.1)
        .restart();
    }
  }

  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event: DragEvent, d: D3Node) {
  d.fx = event.x;
  d.fy = event.y;
  if (
    currentCluster.value &&
    currentCluster.value.nodes.find((n) => n.id === d.id)
  ) {
    currentCluster.value.nodes.forEach((node) => {
      const n = simulation.value?.nodes().find((n) => n.id === node.id) as
        | D3Node
        | undefined;
      if (
        n &&
        n !== d &&
        n.relativeX !== undefined &&
        n.relativeY !== undefined
      ) {
        n.fx = event.x + n.relativeX;
        n.fy = event.y + n.relativeY;
      }
    });
  } else {
    // Single node drag - just update position and tick
    d.x = event.x;
    d.y = event.y;
  }

  tooltipVisible.value = false;
}

function dragEnded(event: DragEvent, d: D3Node) {
  if (!event.active) {
    if (
      currentCluster.value &&
      currentCluster.value.nodes.find((n) => n.id === d.id)
    ) {
      // For cluster drag - completely stop forces and fix final positions
      simulation.value?.stop();

      currentCluster.value.nodes.forEach((node) => {
        const n = simulation.value?.nodes().find((n) => n.id === node.id) as
          | D3Node
          | undefined;
        if (n) {
          // Keep the final positions
          n.x = n.fx || n.x;
          n.y = n.fy || n.y;
          delete n.relativeX;
          delete n.relativeY;
          n.fx = undefined;
          n.fy = undefined;
        }
      });

      // Restore original forces but don't restart simulation
      if (forceLayoutManager.value) {
        forceLayoutManager.value.restoreDefaultForces();
      }
    } else {
      // For single node - gentle release
      simulation.value?.alphaTarget(0).alpha(0.1);
    }
  }

  // Keep final position of dragged node
  d.x = d.fx || d.x;
  d.y = d.fy || d.y;
  d.fx = undefined;
  d.fy = undefined;
}

function fitGraph() {
  if (!chartContainer.value) return;

  const g = d3.select(chartContainer.value).select('g');
  const nodes = g.selectAll('g.node-group');

  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;

  nodes.each(function () {
    const node = d3.select(this).datum() as D3Node;
    minX = Math.min(minX, node.x!);
    maxX = Math.max(maxX, node.x!);
    minY = Math.min(minY, node.y!);
    maxY = Math.max(maxY, node.y!);
  });

  const padding = 50;
  minX -= padding;
  maxX += padding;
  minY -= padding;
  maxY += padding;

  const width = chartContainer.value.clientWidth;
  const height = chartContainer.value.clientHeight;

  const scale = Math.min(width / (maxX - minX), height / (maxY - minY)) * 0.95;

  const svg = d3.select(chartContainer.value).select('svg') as SVGSelection;
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const transform = zoomIdentity
    .translate(width / 2 - centerX * scale, height / 2 - centerY * scale)
    .scale(scale);

  (svg.transition() as SVGTransition)
    .duration(750)
    .call(zoomBehavior.value!.transform, transform);
}

function zoomIn() {
  if (!chartContainer.value || !zoomBehavior.value) return;

  const svg = d3.select(chartContainer.value).select('svg') as SVGSelection;
  const svgNode = svg.node();
  if (!svgNode) return;

  const currentTransform = zoomTransform(svgNode as Element);
  const newTransform = currentTransform.scale(1.5);

  (svg.transition() as SVGTransition)
    .duration(300)
    .call(zoomBehavior.value!.transform, newTransform);
}

function zoomOut() {
  if (!chartContainer.value || !zoomBehavior.value) return;

  const svg = d3.select(chartContainer.value).select('svg') as SVGSelection;
  const svgNode = svg.node();
  if (!svgNode) return;

  const currentTransform = zoomTransform(svgNode as Element);
  const newTransform = currentTransform.scale(1 / 1.5);

  (svg.transition() as SVGTransition)
    .duration(300)
    .call(zoomBehavior.value!.transform, newTransform);
}

function relayoutGraph() {
  if (forceLayoutManager.value) {
    forceLayoutManager.value.relayout();
  }
}

function handleWindowResize() {
  if (!chartContainer.value) return;

  const rect = chartContainer.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  // Update SVG dimensions
  d3.select(chartContainer.value)
    .select('svg')
    .attr('width', width)
    .attr('height', height);

  // Redraw graph if significant size change
  if (forceLayoutManager.value && width > 0 && height > 0) {
    forceLayoutManager.value.updateDimensions(width, height);
  }
}

function openSearch() {
  searchDialog.value?.open();
}

function handleSearchNodeSelect(node: Node) {
  selectNodes([node]);
  currentNode.value = node;
  emit('node-selected', node);
  centerOnNode(node as D3Node);
}

onMounted(() => {
  resizeObserver = new ResizeObserver(handleWindowResize);
  if (chartContainer.value) {
    resizeObserver.observe(chartContainer.value);
  }
  drawGraph();
});

onUnmounted(() => {
  destroyForceLayout();
  resizeObserver.disconnect();
});

watch([() => props.nodes, () => props.edges, showLabels, showImages], () => {
  console.log('Redrawing graph due to data or display changes');
  drawGraph();
});

watch(physicsActive, (newVal) => {
  if (forceLayoutManager.value) {
    if (newVal) {
      forceLayoutManager.value.resumeSimulation();
    } else {
      forceLayoutManager.value.pauseSimulation();
    }
  }
});

watch(nodeSizeMultiplier, () => updateNodeSizes(true));

onMounted(() => {
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.metaKey || event.ctrlKey) {
      isMultiSelectKeyPressed.value = true;

      if (event.key === 'k') {
        event.preventDefault();
        openSearch();
      }
    }
  };

  const handleKeyup = (event: KeyboardEvent) => {
    if (event.key === 'Meta' || event.key === 'Control') {
      isMultiSelectKeyPressed.value = false;
    }
  };

  window.addEventListener('keydown', handleKeydown);
  window.addEventListener('keyup', handleKeyup);

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
    window.removeEventListener('keyup', handleKeyup);
  });
});

defineExpose({
  selectNodes,
  setCurrentCluster,
});
</script>

<style lang="scss">
.d3-graph {
  width: 100%;
  height: 100%;
}

.graph-content {
  height: calc(100vh - 280px);
  width: 100%;
}

.debug-info {
  position: absolute;
  bottom: 8px;
  left: 8px;
  font-size: 12px;
  z-index: 1;
  background: rgba(255, 255, 255, 0.8);
  padding: 4px;
  border-radius: 4px;
}

.node-background {
  fill: transparent;
  pointer-events: all;
  transition:
    stroke-width 0.2s,
    stroke 0.2s,
    fill 0.2s;
}

.node-label {
  fill: #000;
  font-weight: 500;
  text-shadow:
    -1px -1px 0 #fff,
    1px -1px 0 #fff,
    -1px 1px 0 #fff,
    1px 1px 0 #fff;
  paint-order: stroke;
  stroke: #fff;
  stroke-width: 3px;
  stroke-linecap: butt;
  stroke-linejoin: miter;
}

image {
  pointer-events: none;
  transition:
    stroke-width 0.2s,
    stroke 0.2s;
}
</style>
