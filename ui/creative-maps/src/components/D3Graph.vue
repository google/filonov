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
        <template v-slot:thumb-content> {{ nodeSizeMultiplier }}x </template>
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
        @update:model-value="onClusterSelect"
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
        <div class="q-mb-xs" v-for="(tag, idx) of currentNode.tags" :key="tag">
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

<script>
import { defineComponent, onMounted, onUnmounted, watch, ref } from 'vue';
import * as d3 from 'd3';
import { aggregateNodesMetrics } from 'src/helpers/utils';

export default defineComponent({
  props: {
    vertices: {
      type: Array,
      required: true,
    },
    edges: {
      type: Array,
      required: true,
    },
    debug: {
      type: Boolean,
      default: true,
    },
    labelField: {
      type: String,
      default: 'label',
    },
  },

  setup(props, { emit }) {
    const chartContainer = ref(null);
    const tooltipVisible = ref(false);
    const tooltipTarget = ref(null);
    const edgeTooltipVisible = ref(false);
    const edgeTooltipTarget = ref(null);
    const physicsActive = ref(true);
    const simulation = ref(null);
    const zoom = ref(null);
    const showLabels = ref(false);
    const showImages = ref(true);
    const nodeSizeMultiplier = ref(1);
    const clusterIds = ref([]);
    const selectedClusterId = ref(null);
    const currentNode = ref(null);
    const currentEdge = ref(null);
    const currentCluster = ref({
      nodeCount: 0,
      metrics: {},
      nodes: [],
    });
    const imageLoading = ref({
      total: 0,
      current: 0,
      inProgress: false,
    });
    let resizeObserver; //ResizeObserver

    const formatMetricName = (metric) => {
      return metric
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, (str) => str.toUpperCase());
    };

    const formatMetricValue = (value, metric) => {
      if (typeof value !== 'number') return value;

      // if (metric === 'impressions' || metric === 'clicks') {
      //   return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
      // }
      if (metric === 'duration') {
        return `${(value / 60).toFixed(1)} min`;
      }
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
    };

    const findConnectedNodes = (startNode, nodes, edges) => {
      const connected = new Set();
      const queue = [startNode.id.toString()];
      const visited = new Set();

      const adjacencyMap = new Map();
      edges.forEach((edge) => {
        const source = edge.from.toString();
        const target = edge.to.toString();

        if (!adjacencyMap.has(source)) adjacencyMap.set(source, new Set());
        if (!adjacencyMap.has(target)) adjacencyMap.set(target, new Set());

        adjacencyMap.get(source).add(target);
        adjacencyMap.get(target).add(source);
      });

      while (queue.length > 0) {
        const currentId = queue.shift();
        if (visited.has(currentId)) continue;

        visited.add(currentId);
        connected.add(currentId);

        const neighbors = adjacencyMap.get(currentId) || new Set();
        for (const neighborId of neighbors) {
          if (!visited.has(neighborId)) {
            queue.push(neighborId);
          }
        }
      }

      return nodes.filter((n) => connected.has(n.id.toString()));
    };

    const calculateClusterMetrics = (cluster) => {
      if (cluster.nodeCount > 0) {
        cluster.metrics = aggregateNodesMetrics(cluster.nodes);
      }
    };

    const handleNodeClick = (event, node) => {
      node.fx = node.x;
      node.fy = node.y;
      // Stop simulation on click
      if (simulation.value) {
        simulation.value.alpha(0);
        simulation.value.stop();
      }

      tooltipTarget.value = event.currentTarget;
      tooltipVisible.value = true;

      currentNode.value = node;
      emit('node-selected', node);
      onClusterSelect(node.cluster);
    };

    const highlightNode = (event, d) => {
      tooltipTarget.value = event.currentTarget;
      tooltipVisible.value = true;
      currentNode.value = d;
      if (!currentCluster.value) {
        // if there's not selected cluster, highlight the cluster that the node belongs to
        const connectedNodes = findConnectedNodes(
          d,
          props.vertices,
          props.edges,
        );
        highlightNodes(connectedNodes);
      }
      return false;
    };

    const highlightNodes = (nodes) => {
      if (!nodes.length) {
        this.resetHighlight();
        return;
      }
      const connectedIds = new Set(nodes.map((n) => n.id.toString()));

      // Highlight nodes
      d3.select(chartContainer.value)
        .selectAll('g.node-group')
        .transition()
        .duration(200)
        .style('opacity', (node) =>
          connectedIds.has(node.id.toString()) ? 1 : 0.1,
        )
        .each(function () {
          const element = d3.select(this);
          const node = element.datum();
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
        .selectAll('line')
        .transition()
        .duration(200)
        .style('opacity', (link) => {
          const sourceConnected = connectedIds.has(link.source.id.toString());
          const targetConnected = connectedIds.has(link.target.id.toString());
          return sourceConnected && targetConnected ? 0.6 : 0.1;
        });
    };

    const setCurrentCluster = (connectedNodes) => {
      if (!connectedNodes || !connectedNodes.length) {
        currentCluster.value = null;
        resetHighlight();
      } else {
        currentCluster.value = {
          nodes: connectedNodes,
          nodeCount: connectedNodes.length,
          metrics: {},
        };
        highlightNodes(connectedNodes);

        calculateClusterMetrics(currentCluster.value);
      }
      emit('cluster-selected', currentCluster.value);
    };

    const onClusterSelect = (clusterId) => {
      selectedClusterId.value = clusterId;
      if (!clusterId) {
        setCurrentCluster(null);
      } else {
        const clusterNodes = props.vertices.filter(
          (node) => node.cluster === clusterId,
        );
        setCurrentCluster(clusterNodes);
      }
    };

    const resetHighlight = () => {
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
    };

    const preloadImages = async (nodes) => {
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
            imageLoading.value.current = loadedCount;
            resolve(node.image);
          };
          img.onerror = () => {
            loadedCount++;
            imageLoading.value.current = loadedCount;
            reject(node.image);
          };
          img.src = node.image;
        });
      });

      try {
        await Promise.all(imagePromises);
        imageLoading.value.inProgress = false;
        return true;
      } catch (error) {
        console.error('Failed to load some images:', error);
        imageLoading.value.inProgress = false;
        return false;
      }
    };

    const calculateNodeSizes = (nodesCount) => {
      return {
        circleBaseSize:
          Math.max(1, Math.min(1, 40 - Math.log2(nodesCount))) *
          nodeSizeMultiplier.value,

        // Remove Math.min(1, ...) to allow larger initial sizes
        imageBaseSize:
          Math.max(20, 20 - Math.log2(nodesCount)) * nodeSizeMultiplier.value,
      };
    };

    const updateNodeSizes = (restartSimulation = false) => {
      if (!simulation.value || !chartContainer.value) return;

      const { circleBaseSize, imageBaseSize } = calculateNodeSizes(
        props.vertices.length,
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
          const d = d3.select(this).datum();

          if (showImages.value && d?.image) {
            const size = restartSimulation
              ? (d.size || 1) * imageBaseSize
              : Math.min(30, (d.size || 1) * imageBaseSize * 1.5);
            //const size = Math.min(30, (d.size || 1) * imageBaseSize * 1.5);
            // const size1 = (d.size || 1) * imageBaseSize;
            // const size2 = Math.min(30, (d.size || 1) * imageBaseSize * 1.5);
            // console.log({ size1, size2 });
            // const size = Math.min(
            //   30,
            //   (d.size || 1) * imageBaseSize * nodeSizeMultiplier.value * 1.5,
            // );
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
              .attr('r', (d?.size || 1) * circleBaseSize);
          }
        });

      // Update collision forces with new sizes
      simulation.value.force(
        'collision',
        d3
          .forceCollide()
          .radius((d) => {
            const baseRadius =
              showImages.value && d?.image
                ? ((d.size || 1) * imageBaseSize) / 2
                : (d?.size || 1) * circleBaseSize;
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

    const drawGraph = async () => {
      if (!chartContainer.value) return;
      if (simulation.value) {
        simulation.value.stop();
      }
      console.log('drawGraph start, multiplier:', nodeSizeMultiplier.value);

      d3.select(chartContainer.value).selectAll('*').remove();
      clusterIds.value = Array.from(
        new Set(props.vertices.map((node) => node.cluster)),
      ).sort();

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
          onClusterSelect(null);
        });
      const g = svg.append('g');

      const nodes = props.vertices.map((v) => ({
        ...v,
        id: v.id.toString(),
        displayLabel: v[props.labelField] || v.name || v.id.toString(),
      }));

      const links = props.edges.map((e) => ({
        source: e.from.toString(),
        target: e.to.toString(),
        width: e.width || 1,
        similarity: e.similarity,
      }));

      // Wait for images to load
      if (showImages.value) {
        // TODO: to optimize
        await preloadImages(nodes);
      }

      // Separate size calculations for circles and images
      const { circleBaseSize, imageBaseSize } = calculateNodeSizes(
        nodes.length,
      );
      console.log(
        `circleBaseSize: ${circleBaseSize}, imageBaseSize: ${imageBaseSize}`,
      );

      const link = g
        .append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('cursor', 'pointer')
        .on('mouseenter', (event, d) => {
          edgeTooltipTarget.value = event.currentTarget;
          edgeTooltipVisible.value = true;
          currentEdge.value = d;

          // Highlight the hovered edge
          d3.select(event.currentTarget)
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

      const nodeGroup = g
        .append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', 'node-group')
        .attr('cursor', 'pointer')
        .style('pointer-events', 'all') // Ensure group receives events
        .call(
          d3
            .drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended),
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
          let img = element.select('image');
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
            nodes.length,
          );
          const scaledOffset =
            showImages.value && d.image
              ? ((d.size || 1) * imageBaseSize) / 2 // Exactly same as in updateNodeSizes
              : (d.size || 1) * circleBaseSize;
          element
            .append('text')
            .text(d.displayLabel)
            .attr('x', scaledOffset + 5)
            .attr('dy', '.35em')
            .attr('class', 'node-label')
            .style('font-size', `${circleBaseSize * 10}px`)
            .style('pointer-events', 'none');
        }
      });

      // Add mouse events to nodeGroup after node creation
      nodeGroup
        .on('mouseenter', (event, d) => {
          tooltipTarget.value = event.currentTarget;
          tooltipVisible.value = true;
          highlightNode(event, d);
        })
        .on('mouseleave', (event, d) => {
          tooltipVisible.value = false;
          tooltipTarget.value = null;
          resetHighlight(event, d);
        })
        .on('click', (event, d) => {
          event.preventDefault();
          event.stopPropagation();
          handleNodeClick(event, d);
          return false;
        });

      simulation.value = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink(links)
            .id((d) => d.id)
            .distance((link) => {
              // Convert similarity to distance:
              // - Higher similarity (close to 1) = shorter distance
              // - Lower similarity (close to 0) = longer distance
              // You can adjust these values to get the desired visual effect
              const baseDistance = 200; // maximum distance
              const minDistance = 30; // minimum distance
              const similarity = link.similarity || 0.5; // default to 0.5 if not present

              // Linear interpolation between max and min distance based on similarity
              //return baseDistance * (1 - similarity) + minDistance;
              return baseDistance * (1 - similarity) + minDistance;
              //return baseDistance * Math.pow(1 - similarity, 2) + minDistance;
            }), //.distance(50), // Back to original
        )
        .force(
          'charge',
          d3
            .forceManyBody()
            .strength(-100) // Back to original strength
            .distanceMax(width / 2), // Back to original
        )
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force(
          'collision',
          d3
            .forceCollide()
            .radius((d) => {
              const baseRadius =
                showImages.value && d.image
                  ? Math.min(30, (d.size || 1) * imageBaseSize * 1.5) / 2
                  : (d.size || 1) * circleBaseSize;
              return baseRadius * 2.5; // Increased collision radius but not as extreme
            })
            .strength(0.8) // Slightly reduced from 1
            .iterations(2), // Back to original
        )
        .alphaDecay(0.01) // Original decay
        .velocityDecay(0.3) // Original damping
        .alpha(0.3) // Reduced initial energy
        .alphaTarget(0);
      if (!physicsActive.value) {
        simulation.value.stop();
      }

      updateNodeSizes(true);

      simulation.value.on('tick', () => {
        link
          .attr('x1', (d) => d.source.x)
          .attr('y1', (d) => d.source.y)
          .attr('x2', (d) => d.target.x)
          .attr('y2', (d) => d.target.y);

        nodeGroup.attr('transform', (d) => `translate(${d.x},${d.y})`);
      });

      function dragstarted(event, d) {
        if (!event.active) simulation.value.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
        tooltipVisible.value = false;
      }

      function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event, d) {
        if (!event.active) simulation.value.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      zoom.value = d3
        .zoom()
        .scaleExtent([0.05, 4])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });

      svg.call(zoom.value);

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
    };

    const fitGraph = () => {
      if (!chartContainer.value || !simulation.value) return;

      const g = d3.select(chartContainer.value).select('g');
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

      const padding = 50;
      minX -= padding;
      maxX += padding;
      minY -= padding;
      maxY += padding;

      const width = chartContainer.value.clientWidth;
      const height = chartContainer.value.clientHeight;

      const scale =
        Math.min(width / (maxX - minX), height / (maxY - minY)) * 0.95;

      const svg = d3.select(chartContainer.value).select('svg');

      const transform = d3.zoomIdentity
        .translate(
          width / 2 - ((minX + maxX) / 2) * scale,
          height / 2 - ((minY + maxY) / 2) * scale,
        )
        .scale(scale);

      svg.transition().duration(750).call(zoom.value.transform, transform);
    };

    const handleResize = () => {
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
        simulation.value.force('center', d3.forceCenter(width / 2, height / 2));
        simulation.value.alpha(0.3).restart();
      }
    };

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
      [() => props.vertices, () => props.edges, showLabels, showImages],
      (newValues) => {
        console.log('rerendering');
        console.log(newValues);
        drawGraph();
      },
      { deep: true },
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

    return {
      chartContainer,
      imageLoading,
      clusterIds,
      selectedClusterId,
      onClusterSelect,
      showLabels,
      showImages,
      physicsActive,
      nodeSizeMultiplier,
      tooltipVisible,
      tooltipTarget,
      edgeTooltipVisible,
      edgeTooltipTarget,
      currentCluster,
      currentNode,
      currentEdge,
      formatMetricName,
      formatMetricValue,
      highlightNodes,
      fitGraph,
      setCurrentCluster,
    };
  },
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
