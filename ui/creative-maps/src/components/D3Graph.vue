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
        icon="fit_screen"
        @click="fitGraph"
        color="primary"
      />
      <q-select
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
    </div>
    <div ref="chartContainer" class="graph-content"></div>
    <!-- <div v-if="debug" style="font-size: 12px; margin-top: 10px">
      Vertices: {{ vertices.length }}, Edges: {{ edges.length }}
    </div> -->
    <q-tooltip
      v-model="tooltipVisible"
      :target="tooltipTarget"
      anchor="bottom middle"
      self="top middle"
      :offset="[0, 10]"
      v-if="currentNode"
    >
      <div class="text-body2">
        <div class="text-weight-bold q-mb-sm">Metrics:</div>
        <div
          v-for="(value, metric) in currentNode.info"
          :key="metric"
          class="q-mb-xs"
        >
          {{ formatMetricName(metric) }}: {{ formatMetricValue(value, metric) }}
        </div>
        <div class="text-weight-bold q-mb-sm">Tags:</div>
        <div
          class="q-mb-xs"
          v-for="(tag, idx) of currentNode.tags"
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
      v-if="currentEdge"
    >
      <div class="text-body2">
        <div class="text-weight-bold">
          Similarity: {{ (currentEdge?.similarity || 0).toFixed(3) }}
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
import { onMounted, onUnmounted, watch, ref, markRaw, defineExpose } from 'vue';
import * as d3 from 'd3';
import { ClusterInfo, Edge, Node } from 'components/models';
import { aggregateNodesMetrics } from 'src/helpers/graph';
import { formatMetricValue } from 'src/helpers/utils';
import {
  Simulation,
  SimulationNodeDatum,
  SimulationLinkDatum,
  ForceLink,
} from 'd3-force';
import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceCenter,
  forceSimulation,
} from 'd3-force';
import { D3DragEvent, drag } from 'd3-drag';
import { zoom, ZoomBehavior, zoomIdentity } from 'd3-zoom';
import { Transition } from 'd3-transition';
import { Selection } from 'd3-selection';

type D3Node = Node &
  SimulationNodeDatum & { initialX?: number; initialY?: number };
type D3Edge = Edge & SimulationLinkDatum<D3Node>;

type SVGSelection = Selection<SVGSVGElement, unknown, null, undefined>;
type SVGTransition = Transition<SVGSVGElement, unknown, null, undefined>;
type DragEvent = D3DragEvent<SVGGElement, D3Node, D3Node>;

interface Props {
  nodes: Node[];
  edges: Edge[];
  clusters: ClusterInfo[];
  debug?: boolean;
  labelField?: string;
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
const currentEdge = ref<Edge | null>(null);
const currentCluster = ref<ClusterInfo | null>(null);
const imageLoading = ref({
  total: 0,
  current: 0,
  inProgress: false,
});
let resizeObserver: ResizeObserver;

const formatMetricName = (metric: string) => {
  return metric
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase());
};

function handleNodeClick(event: Event, node: D3Node) {
  node.fx = node.x;
  node.fy = node.y;
  // Stop simulation on click
  if (simulation.value) {
    simulation.value.alpha(0);
    simulation.value.stop();
  }

  tooltipTarget.value = event.currentTarget as HTMLElement;
  tooltipVisible.value = true;

  currentNode.value = node;
  emit('node-selected', node);
  setCurrentCluster(node.cluster);
}

function getCluster(clusterId: string) {
  return props.clusters.find((c) => c.id === clusterId);
}

function highlightNode(event: Event, d: Node) {
  tooltipTarget.value = event.currentTarget as HTMLElement;
  tooltipVisible.value = true;
  currentNode.value = d;
  console.log(currentCluster.value);
  if (!currentCluster.value) {
    // if there's not selected cluster, highlight the cluster that the node belongs to
    // const connectedNodes = findConnectedNodes(
    //   d,
    //   nodes,
    //   links,
    // );
    const connectedNodes = getCluster(d.cluster)?.nodes || [];
    //console.log('highlightNodes', connectedNodes);
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
            isConnected ? 'drop-shadow(0 0 3px rgba(255,0,0,0.5))' : 'none',
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
      const sourceConnected = connectedIds.has(
        link.from.toString(),
        //link.source.id ? link.source.id : link.source.toString(),
      );
      const targetConnected = connectedIds.has(
        link.to.toString(),
        //link.target.id ? link.target.id : link.target.toString(),
      );
      if (sourceConnected && targetConnected) {
        console.log('highlighting ', link);
      }
      return sourceConnected && targetConnected ? 0.6 : 0.1;
    });
}

// select arbitrary number of nodes, it's similar to selecting a cluster (in setCurrentCluster),
// but nodes can be not connected
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function selectNodes(connectedNodes: Node[] | null, description?: string) {
  if (!connectedNodes || !connectedNodes.length) {
    currentCluster.value = null;
    resetHighlight();
  } else {
    currentCluster.value = {
      id: '',
      description,
      nodes: connectedNodes,
      metrics: aggregateNodesMetrics(connectedNodes),
    };
    highlightNodes(connectedNodes);
  }
  emit('cluster-selected', currentCluster.value);
}

function setCurrentCluster(clusterId: string | null) {
  selectedClusterId.value = clusterId;
  if (!clusterId) {
    currentCluster.value = null;
    resetHighlight();
  } else {
    const clusterNodes = getCluster(clusterId)!.nodes;
    currentCluster.value = getCluster(clusterId) || null;
    highlightNodes(clusterNodes);
  }
  emit('cluster-selected', currentCluster.value);
}

function resetHighlight() {
  tooltipVisible.value = false;
  currentNode.value = null;
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
  imageLoading.value = {
    total: imagesToLoad.length,
    current: 0,
    inProgress: true,
  };

  const imagePromises = imagesToLoad.map((node) => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        loadedCount++;
        imageLoading.value = {
          total: imagesToLoad.length,
          current: loadedCount,
          inProgress: true,
        };
        resolve(node.image);
      };
      img.onerror = () => {
        loadedCount++;
        imageLoading.value = {
          total: imagesToLoad.length,
          current: loadedCount,
          inProgress: false,
        };
        reject(node.image);
      };
      img.src = node.image;
    });
  });

  try {
    await Promise.all(imagePromises);
    imageLoading.value = {
      total: imagesToLoad.length,
      current: loadedCount,
      inProgress: false,
    };
    return true;
  } catch (error) {
    console.error('Failed to load some images:', error);
    imageLoading.value = {
      total: imagesToLoad.length,
      current: loadedCount,
      inProgress: false,
    };
    return false;
  }
}

function calculateNodeSizes(nodesCount: number) {
  return {
    circleBaseSize:
      Math.max(1, Math.min(1, 40 - Math.log2(nodesCount))) *
      nodeSizeMultiplier.value,

    // Remove Math.min(1, ...) to allow larger initial sizes
    imageBaseSize:
      Math.max(20, 20 - Math.log2(nodesCount)) * nodeSizeMultiplier.value,
  };
}

const updateNodeSizes = (restartSimulation = false) => {
  if (!simulation.value || !chartContainer.value) return;

  const { circleBaseSize, imageBaseSize } = calculateNodeSizes(
    props.nodes.length,
  );

  // console.log('updateNodeSizes:', {
  //   multiplier: nodeSizeMultiplier.value,
  //   circleBaseSize,
  //   imageBaseSize,
  //   showImages: showImages.value,
  // });

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

  // Update collision forces with new sizes
  simulation.value.force(
    'collision',
    forceCollide<D3Node>()
      .radius((d) => {
        const baseRadius =
          showImages.value && d.image
            ? (d.size * imageBaseSize) / 2
            : d.size * circleBaseSize;
        return baseRadius * 2;
      })
      .strength(0.8)
      .iterations(2),
  );

  // Only restart simulation if requested
  if (restartSimulation) {
    simulation.value.alpha(0.3).restart();
  }
};

function prepositionNodes() {
  if (!chartContainer.value) return;
  // Position clusters in a circle
  const rect = chartContainer.value!.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  // const centerX = width / 2;
  // const centerY = height / 2;
  // const radius = Math.min(width, height) / 3;
  //const angleStep = (2 * Math.PI) / clusters.size;
  const gridSize = Math.ceil(Math.sqrt(props.clusters.length));
  const gridCellWidth = width / gridSize;
  const gridCellHeight = height / gridSize;
  //let angle = 0;
  //const padding = 50; // Padding between clusters

  // For each cluster
  props.clusters.forEach((cluster, index) => {
    //clusters.forEach((clusterNodes) => {
    // const clusterX = centerX + radius * Math.cos(angle);
    // const clusterY = centerY + radius * Math.sin(angle);
    const row = Math.floor(index / gridSize);
    const col = index % gridSize;

    // Center of the grid cell
    const clusterX = (col + 0.5) * gridCellWidth;
    const clusterY = (row + 0.5) * gridCellHeight;

    // Position nodes within cluster in a smaller circle
    const clusterRadius = Math.sqrt(cluster.nodes.length) * 30;
    cluster.nodes.forEach((node: D3Node, i) => {
      const nodeAngle = (2 * Math.PI * i) / cluster.nodes.length;
      // node.x = clusterX + clusterRadius * Math.cos(nodeAngle);
      // node.y = clusterY + clusterRadius * Math.sin(nodeAngle);
      // // Set initial positions for force simulation
      // node.fx = node.x;
      // node.fy = node.y;
      node.initialX = clusterX + clusterRadius * Math.cos(nodeAngle);
      node.initialY = clusterY + clusterRadius * Math.sin(nodeAngle);
      // Start with fixed positions
      node.fx = node.initialX;
      node.fy = node.initialY;
    });

    //angle += angleStep;  });
  });

  // Gradually release positions
  const releaseSteps = 10;
  for (let step = 0; step < releaseSteps; step++) {
    setTimeout(() => {
      const factor = Math.pow(1 - step / releaseSteps, 2); // Quadratic easing
      props.nodes.forEach((node: D3Node) => {
        if (node.fx !== null) {
          node.fx = node.initialX! + (1 - factor) * (node.x! - node.initialX!);
          node.fy = node.initialY! + (1 - factor) * (node.y! - node.initialY!);
        }
      });

      // On last step, release completely
      if (step === releaseSteps - 1) {
        props.nodes.forEach((node: D3Node) => {
          node.fx = undefined;
          node.fy = undefined;
          delete node.initialX;
          delete node.initialY;
        });
      }
    }, step * 100); // Spread over 2 seconds
  }
}

async function drawGraph() {
  if (!chartContainer.value) return;
  if (simulation.value) {
    simulation.value.stop();
  }
  console.log('drawGraph start, multiplier:', nodeSizeMultiplier.value);

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

  props.nodes.forEach((node: Node) => {
    node.size = node.size || 10;
  });

  props.edges.forEach((edge: Edge) => {
    (edge as D3Edge).source = edge.from; // D3 will resolve this to the actual node
    (edge as D3Edge).target = edge.to; // D3 will resolve this to the actual node
    edge.width = edge.width || 1;
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
  console.log(
    `circleBaseSize: ${circleBaseSize}, imageBaseSize: ${imageBaseSize}`,
  );

  console.log('Creating links');
  const link = g
    .append('g')
    .selectAll<SVGLineElement, D3Edge>('line')
    .data<D3Edge>(props.edges as D3Edge[])
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('cursor', 'pointer')
    .on('mouseenter', (event: Event, d: Edge) => {
      edgeTooltipTarget.value = event.currentTarget as HTMLElement;
      edgeTooltipVisible.value = true;
      currentEdge.value = d;

      // Highlight the hovered edge
      d3.select(event.currentTarget as HTMLElement)
        .transition()
        .duration(200)
        .attr('stroke', '#ff0000')
        .attr('stroke-opacity', 1)
        .attr('stroke-width', 3);
    })
    .on('mouseleave', (event) => {
      edgeTooltipVisible.value = false;
      currentEdge.value = null;

      // Reset edge style
      d3.select(event.currentTarget)
        .transition()
        .duration(200)
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 1);
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
      element
        .selectAll('.node-background')
        .data([d])
        .join('circle')
        .attr('class', 'node-background')
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
      tooltipTarget.value = event.currentTarget as HTMLElement;
      tooltipVisible.value = true;
      highlightNode(event, d);
    })
    .on('mouseleave', () => {
      tooltipVisible.value = false;
      tooltipTarget.value = undefined;
      resetHighlight();
    })
    .on('click', (event: Event, d: Node) => {
      event.preventDefault();
      event.stopPropagation();
      handleNodeClick(event, d);
      return false;
    });

  console.log('Setting up simulation');
  // Pre-position nodes before simulation
  prepositionNodes();

  simulation.value = markRaw(
    forceSimulation<D3Node>(props.nodes)
      .force(
        'link',
        forceLink<D3Node, D3Edge>(props.edges as D3Edge[])
          .id((d) => d.id)
          .strength(0.2) // Very weak force
          .distance(50), // Fixed distance for now
      )
      .force(
        'charge',
        forceManyBody()
          .strength(-100)
          .distanceMax(width / 3),
      )
      .force('center', forceCenter(width / 2, height / 2))
      .force(
        'collision',
        forceCollide<D3Node>()
          .radius((d) => {
            const baseRadius =
              showImages.value && d.image
                ? Math.min(30, d.size * imageBaseSize * 1.5) / 2
                : d.size * circleBaseSize;
            return baseRadius * 2.5;
          })
          .strength(0.5),
      )
      .alphaDecay(0.01)
      .velocityDecay(0.2)
      .alpha(0.5)
      .alphaTarget(0),
  );
  if (!physicsActive.value) {
    simulation.value
      .force('link', null)
      .force('charge', null)
      .force('center', null)
      .force('collision', null)
      .stop();
  }
  if (props.edges.length < 500) {
    setTimeout(() => {
      console.log('Enhancing force layout...');

      const baseDistance = 200;
      const minDistance = 30;
      const linkDistances = new Map();
      props.edges.forEach((edge) => {
        const similarity = edge.similarity || 0.5;
        const distance = Math.max(
          minDistance,
          baseDistance * (1 - similarity) + minDistance,
        );
        linkDistances.set(edge, isFinite(distance) ? distance : minDistance);
      });
      simulation.value!.force(
        'charge',
        forceManyBody().strength(-500).distanceMax(width),
      );
      simulation
        .value!.force<ForceLink<D3Node, D3Edge>>('link')!
        .strength(0.5)
        .distance((link) => linkDistances.get(link));
      // Reheat simulation but not too much
      simulation.value!.alpha(0.1).restart();
    }, 3000);
  }

  updateNodeSizes(true);

  console.log('Setting up tick handler');
  simulation.value.on('tick', () => {
    link
      .attr('x1', (d) => (d.source as D3Node).x!)
      .attr('y1', (d) => (d.source as D3Node).y!)
      .attr('x2', (d) => (d.target as D3Node).x!)
      .attr('y2', (d) => (d.target as D3Node).y!);

    nodeGroup.attr('transform', (d: D3Node) => `translate(${d.x},${d.y})`);
  });

  function dragStarted(event: DragEvent, d: D3Node) {
    if (!event.active) simulation.value?.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
    tooltipVisible.value = false;
  }

  function dragged(event: DragEvent, d: D3Node) {
    d.fx = event.x;
    d.fy = event.y;
    tooltipVisible.value = false;
  }

  function dragEnded(event: DragEvent, d: D3Node) {
    if (!event.active) simulation.value?.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  zoomBehavior.value = zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.05, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });

  svg.call(zoomBehavior.value);

  // After the simulation has been created and nodes positioned,
  // calculate the bounds and set initial zoom:
  /*
      simulation.value.on('end', () => {
        // Get the bounds of all nodes
        const nodes = g.selectAll('g.node-group');
        let minX = Infinity,
          maxX = -Infinity,
          minY = Infinity,
          maxY = -Infinity;

        nodes.each(function () {
          const node = d3.select(this).datum();
          minX = Math.min(minX, node.x);
          maxX = Math.max(maxX, node.x);
          minY = Math.min(minY, node.y);
          maxY = Math.max(maxY, node.y);
        });

        // Add padding
        const padding = 50;
        minX -= padding;
        maxX += padding;
        minY -= padding;
        maxY += padding;

        // Calculate the scale and translate to fit the bounds
        const scale =
          Math.min(width / (maxX - minX), height / (maxY - minY)) * 0.95; // 0.95 adds a little margin

        const transform = d3.zoomIdentity
          .translate(
            width / 2 - ((minX + maxX) / 2) * scale,
            height / 2 - ((minY + maxY) / 2) * scale,
          )
          .scale(scale);

        // Apply the transform smoothly
        svg.transition().duration(750).call(zoom.transform, transform);
      });
      */
  console.log('drawGraph completed');
}

function fitGraph() {
  if (!chartContainer.value || !simulation.value) return;

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

  const transform = zoomIdentity
    .translate(
      width / 2 - ((minX + maxX) / 2) * scale,
      height / 2 - ((minY + maxY) / 2) * scale,
    )
    .scale(scale);

  (svg.transition() as SVGTransition)
    .duration(750)
    .call(zoomBehavior.value!.transform, transform);
}

function handleResize() {
  if (!chartContainer.value) return;

  const rect = chartContainer.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  // Update SVG dimensions
  d3.select(chartContainer.value)
    .select('svg')
    .attr('width', width)
    .attr('height', height);

  // Update force simulation center
  if (simulation.value) {
    simulation.value.force('center', forceCenter(width / 2, height / 2));
    simulation.value.alpha(0.3).restart();
  }
}

onMounted(() => {
  resizeObserver = new ResizeObserver(handleResize);
  if (chartContainer.value) {
    resizeObserver.observe(chartContainer.value);
  }
  drawGraph();
});

// Cleanup
onUnmounted(() => {
  if (simulation.value) simulation.value.stop();
  resizeObserver.disconnect();
});

watch(
  [() => props.nodes, () => props.edges, showLabels, showImages],
  (newValues) => {
    console.log('rerendering');
    console.log(newValues);
    drawGraph();
  },
  //{ deep: true },
);

watch(
  () => physicsActive,
  (newVal) => {
    if (newVal.value) {
      if (simulation.value) simulation.value.restart();
    } else {
      if (simulation.value) simulation.value.stop();
    }
  },
  { deep: true },
);

watch(nodeSizeMultiplier, () => updateNodeSizes(true)); // restart when size changes

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
  height: calc(100vh - 240px);
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
