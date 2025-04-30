import { ref, markRaw, Ref, watchEffect } from 'vue';
import {
  Simulation,
  SimulationNodeDatum,
  SimulationLinkDatum,
  forceCollide,
  forceLink,
  forceManyBody,
  forceCenter,
  forceSimulation,
} from 'd3-force';
import { Node, Edge, ClusterInfo } from 'components/models';

// Type definitions
export type D3Node = Node &
  SimulationNodeDatum & {
    initialX?: number;
    initialY?: number;
    relativeX?: number;
    relativeY?: number;
    x?: number | undefined | null;
    y?: number | undefined | null;
  };

export type D3Edge = Edge & SimulationLinkDatum<D3Node>;

export type ForceLayoutStrategy = 'default' | 'experimental';

export interface ForceLayoutOptions {
  physicsActive?: Ref<boolean>;
  onTick?: (this: Simulation<D3Node, D3Edge>) => void;
  getCollisionRadius?: (node: D3Node) => number;
  width?: number;
  height?: number;
}

export interface ClusterCenter {
  x: number;
  y: number;
  size: number;
}

export class ForceLayoutManager {
  private simulation: Simulation<D3Node, D3Edge> | null = null;
  private nodes: D3Node[] = [];
  private edges: D3Edge[] = [];
  private clusters: ClusterInfo[] = [];
  private clusterCenters = new Map<string, ClusterCenter>();
  private strategy: ForceLayoutStrategy = 'default';
  private options: ForceLayoutOptions;
  private width: number;
  private height: number;
  private getCollisionRadius: (node: D3Node) => number;
  private virtualEdges: D3Edge[] = [];

  constructor(
    nodes: Node[],
    edges: Edge[],
    clusters: ClusterInfo[],
    options: ForceLayoutOptions,
  ) {
    this.nodes = nodes as D3Node[];
    this.edges = edges as D3Edge[];
    this.clusters = clusters;
    this.options = options;
    this.width = options.width || 800;
    this.height = options.height || 600;
    this.getCollisionRadius =
      options.getCollisionRadius ||
      ((d) => {
        return d.size * 5; // a simple default if none provided
      });
  }

  /**
   * Set the layout strategy to use
   */
  setStrategy(strategy: ForceLayoutStrategy): void {
    this.strategy = strategy;
  }

  /**
   * Initialize and start the force simulation
   */
  initSimulation(): Simulation<D3Node, D3Edge> {
    // Create the simulation with appropriate forces
    const sim = this.createSimulation();

    // Set up tick handler if provided
    if (this.options.onTick) {
      sim.on('tick', this.options.onTick);
    }

    // Store the simulation
    this.simulation = markRaw(sim);

    // Handle physics toggle
    if (this.options.physicsActive) {
      watchEffect(() => {
        if (this.options.physicsActive?.value) {
          this.resumeSimulation();
        } else {
          this.pauseSimulation();
        }
      });
    }

    return this.simulation;
  }

  /**
   * Resume the simulation
   */
  resumeSimulation(): void {
    if (this.simulation) {
      this.simulation.alpha(0.3).restart();
    }
  }

  /**
   * Pause the simulation
   */
  pauseSimulation(): void {
    if (this.simulation) {
      this.simulation.stop();
    }
  }

  /**
   * Stop and destroy the simulation
   */
  destroySimulation(): void {
    if (this.simulation) {
      this.simulation
        .force('link', null)
        .force('charge', null)
        .force('center', null)
        .force('collision', null)
        .force('cluster', null)
        .stop();
      this.simulation.on('tick', null);
      this.simulation = null;
    }
  }

  /**
   * Update collision radius in the simulation
   * This only updates the physics, not visual appearance
   */
  updateCollisionRadius(): void {
    if (!this.simulation) return;

    // Update collision force with current radius function
    this.simulation.force(
      'collision',
      forceCollide<D3Node>()
        .radius((d) => {
          // Use the function provided by the component
          const baseRadius = this.getCollisionRadius(d);
          return baseRadius;
        })
        .strength(0.8)
        .iterations(2),
    );

    this.simulation.alpha(0.3).restart();
  }

  /**
   * Restart layout with current settings
   */
  relayout(): void {
    this.prepositionNodes();
    if (this.simulation) {
      this.simulation.alpha(1).restart();
    }
  }

  /**
   * Restore forces after a drag operation - needs to maintain cluster separation
   */
  restoreDefaultForces(): void {
    if (!this.simulation) return;
    if (!this.strategy) {
      // CRITICAL: Use stronger center force and weaker charge after drag
      this.simulation
        // Weaker charge
        .force('charge', forceManyBody().strength(-50).distanceMax(150))
        // Same link force
        .force(
          'link',
          forceLink<D3Node, D3Edge>(this.edges)
            .id((d) => d.id)
            .strength(0.3)
            .distance(30),
        )
        // STRONGER center force to prevent flying apart
        .force(
          'center',
          forceCenter(this.width / 2, this.height / 2).strength(0.02),
        )
        // Higher decay to dampen movement
        .velocityDecay(0.8)
        .alpha(0.1)
        .restart();
    } else {
      // Default strategy restoration
      this.simulation.force('charge', forceManyBody().strength(-50));
      this.simulation.force(
        'link',
        forceLink<D3Node, D3Edge>(this.edges)
          .id((d) => d.id)
          .strength(0.2)
          .distance(50),
      );
      this.simulation.force(
        'center',
        forceCenter(this.width / 2, this.height / 2).strength(0.01),
      );
      this.simulation.alphaDecay(0.02).alpha(0.3).alphaMin(0.001).restart();
    }
  }

  /**
   * Update simulation for new container dimensions
   */
  updateDimensions(width: number, height: number): void {
    if (!this.simulation) return;

    // Store new dimensions
    this.width = width;
    this.height = height;

    if (this.simulation) {
      // Update center force with new dimensions
      this.simulation.force('center', forceCenter(width / 2, height / 2));

      // Restart simulation with low alpha to allow gentle adjustment
      this.simulation.alpha(0.3).restart();
    }
  }

  /**
   * Create the appropriate simulation based on strategy
   */
  private createSimulation(): Simulation<D3Node, D3Edge> {
    let sim: Simulation<D3Node, D3Edge>;
    this.prepositionNodes();

    switch (this.strategy) {
      case 'experimental':
        sim = this.createExperimentalSimulation();
        break;
      case 'default':
      default:
        sim = this.createDefaultSimulation();
        break;
    }

    return sim;
  }

  /**
   * Create default D3 force simulation
   */
  private createDefaultSimulation(): Simulation<D3Node, D3Edge> {
    return forceSimulation<D3Node>(this.nodes)
      .force(
        'link',
        forceLink<D3Node, D3Edge>(this.edges)
          .id((d) => d.id)
          .strength(0.01) // Very weak
          .distance((d) => {
            // Check if link is within same cluster
            const sourceNode = this.nodes.find((n) => n.id === d.source);
            const targetNode = this.nodes.find((n) => n.id === d.target);
            return sourceNode?.cluster === targetNode?.cluster ? 30 : 200;
          }),
      )
      .force('charge', forceManyBody().strength(-5).distanceMax(150))
      .force(
        'center',
        forceCenter(this.width / 2, this.height / 2).strength(0.01),
      )
      .force(
        'collision',
        forceCollide<D3Node>()
          .radius((d) => {
            return this.getCollisionRadius(d);
          })
          .strength(0.8)
          .iterations(2),
      )
      .alphaDecay(0.02)
      .alpha(0.3);
  }

  /*
  private createExperimentalSimulation(): Simulation<D3Node, D3Edge> {
    // Ensure cluster centers are calculated before simulation starts
    if (this.clusterCenters.size === 0) {
      console.warn(
        'Cluster centers not calculated before simulation start. Running prepositionNodesExp again.',
      );
      this.prepositionNodesExp(); // Recalculate if somehow missed
    }

    // Let the force simulation use the natural connections
    return (
      forceSimulation<D3Node>(this.nodes)
        // Stronger link force to keep connected nodes together
        .force(
          'link',
          forceLink<D3Node, D3Edge>(this.edges)
            .id((d) => d.id)
            .strength(0.5) // Strong links to preserve structure
            .distance(50), // Keep connected nodes close
        )
        // Moderate collision to prevent overlap
        .force(
          'collision',
          forceCollide<D3Node>()
            .radius((d) => this.getCollisionRadius(d))
            .strength(0.7)
            .iterations(2),
        )
        // Use the reduced charge strength
        .force('charge', forceManyBody().strength(-50).distanceMax(300))
        // Very weak center force just to keep nodes on screen
        .force(
          'center',
          forceCenter(this.width / 2, this.height / 2).strength(0.05),
        )
        // Add the custom cluster force
        .force('cluster', this.clusterForce)
        // Standard settings
        .velocityDecay(0.6)
        .alpha(0.4) // Slightly lower start energy
        .alphaDecay(0.015) // Slightly faster decay
        .alphaMin(0.001) // Lower minimum to allow more organization time
    );
  }
  */
  private createExperimentalSimulation(): Simulation<D3Node, D3Edge> {
    if (this.clusterCenters.size === 0) {
      this.prepositionNodesExp();
    }

    // Combine real edges with virtual ones
    const allEdges = [...this.edges, ...this.virtualEdges];

    return (
      forceSimulation<D3Node>(this.nodes)
        // Use combined edges for layout
        .force(
          'link',
          forceLink<D3Node, D3Edge>(allEdges)
            .id((d) => d.id)
            .strength((d) => {
              // Real edges are stronger than virtual ones
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              return (d as any).isVirtual ? 0.3 : 0.7;
            })
            .distance((d) => {
              // Keep nodes connected by real edges closer
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              return (d as any).isVirtual ? 30 : 20;
            }),
        )
        // Low charge force to minimize repulsion
        .force('charge', forceManyBody().strength(-30).distanceMax(100))
        // Standard collision
        .force(
          'collision',
          forceCollide<D3Node>()
            .radius((d) => this.getCollisionRadius(d))
            .strength(0.7)
            .iterations(2),
        )
        // Center force to keep graph centered
        .force(
          'center',
          forceCenter(this.width / 2, this.height / 2).strength(0.1),
        )
        // Standard simulation settings
        .velocityDecay(0.6)
        .alpha(0.3)
        .alphaDecay(0.02)
    );
  }

  /**
   * Preposition nodes based on selected strategy
   */
  private prepositionNodes(): void {
    console.log('prepositionNodes: ' + this.strategy);
    this.clusterCenters.clear();

    if (this.strategy === 'experimental') {
      this.prepositionNodesExp();
    } else {
      this.prepositionNodesDefault();
    }
  }

  private prepositionNodesDefault() {
    const rect = { width: this.width, height: this.height };
    const width = rect.width;
    const height = rect.height;
    const centerX = width / 2;
    const centerY = height / 2;

    const singleNodeClusters = this.clusters.filter(
      (c) => c.nodes.length === 1,
    );
    const multiNodeClusters = this.clusters.filter((c) => c.nodes.length > 1);

    // Position multi-node clusters in a smaller central area
    const centralAreaSize = Math.min(width, height) / 3;
    multiNodeClusters.forEach((cluster, index) => {
      const angle = (2 * Math.PI * index) / multiNodeClusters.length;
      const clusterX = centerX + (centralAreaSize / 2) * Math.cos(angle);
      const clusterY = centerY + (centralAreaSize / 2) * Math.sin(angle);

      // Position nodes in a tight circle within cluster
      const clusterRadius = Math.sqrt(cluster.nodes.length) * 15;
      cluster.nodes.forEach((node: D3Node, i) => {
        const nodeAngle = (2 * Math.PI * i) / cluster.nodes.length;
        node.x = clusterX + clusterRadius * Math.cos(nodeAngle);
        node.y = clusterY + clusterRadius * Math.sin(nodeAngle);
      });
    });

    // Group single nodes by their connections
    const connectedToCenter = new Map<string, number>(); // Use node ID as key
    singleNodeClusters.forEach((cluster) => {
      const node = cluster.nodes[0];
      const connections = this.edges.filter(
        (e) =>
          (e.from === node.id || e.to === node.id) &&
          multiNodeClusters.some((mc) =>
            mc.nodes.some((n) => n.id === e.from || n.id === e.to),
          ),
      ).length;
      connectedToCenter.set(node.id.toString(), connections); // Use node ID
    });

    // Position single nodes in concentric circles based on connection count
    const maxConnections = Math.max(
      0,
      ...Array.from(connectedToCenter.values()),
    );
    const ringCount = maxConnections + 1;
    const ringSpacing = centralAreaSize / 2 / ringCount;

    singleNodeClusters.forEach((cluster) => {
      const node = cluster.nodes[0] as D3Node;
      const connections = connectedToCenter.get(node.id.toString()) || 0;
      const ring = ringCount - connections;
      const ringRadius = centralAreaSize + ring * ringSpacing;
      const angle = Math.random() * 2 * Math.PI;

      node.x = centerX + ringRadius * Math.cos(angle);
      node.y = centerY + ringRadius * Math.sin(angle);
    });
  }

  private prepositionNodesExp(): void {
    this.clusterCenters.clear();
    this.virtualEdges = [];

    // Group nodes by their assigned cluster
    const clusterMap = new Map<string, D3Node[]>();
    this.nodes.forEach((node) => {
      if (!node.cluster) return;

      const clusterId = node.cluster.toString();
      if (!clusterMap.has(clusterId)) {
        clusterMap.set(clusterId, []);
      }
      clusterMap.get(clusterId)!.push(node);
    });

    // Position cluster centers in a grid
    const clusterIds = Array.from(clusterMap.keys());
    const gridSize = Math.ceil(Math.sqrt(clusterIds.length));
    const cellSize = (Math.min(this.width, this.height) * 0.75) / gridSize;
    const centerX = this.width / 2;
    const centerY = this.height / 2;

    // Create virtual edges to hold clusters together
    clusterIds.forEach((clusterId, index) => {
      const row = Math.floor(index / gridSize);
      const col = index % gridSize;

      // Position cluster with some randomness to avoid perfect grid
      const offsetX = (Math.random() - 0.5) * cellSize * 0.2;
      const offsetY = (Math.random() - 0.5) * cellSize * 0.2;
      const clusterX =
        centerX + (col - gridSize / 2 + 0.5) * cellSize + offsetX;
      const clusterY =
        centerY + (row - gridSize / 2 + 0.5) * cellSize + offsetY;

      const clusterNodes = clusterMap.get(clusterId)!;

      // Store cluster center
      this.clusterCenters.set(clusterId, {
        x: clusterX,
        y: clusterY,
        size: clusterNodes.length,
      });

      // Create virtual edges between nodes in this cluster
      // This helps keep them together even without real connections
      for (let i = 0; i < clusterNodes.length; i++) {
        // Initial node positions in a small circle around cluster center
        const angle = (2 * Math.PI * i) / clusterNodes.length;
        const radius = Math.sqrt(clusterNodes.length) * 5;

        clusterNodes[i].x = clusterX + radius * Math.cos(angle);
        clusterNodes[i].y = clusterY + radius * Math.sin(angle);

        // Connect each node to a few others in same cluster with virtual edges
        for (let j = 1; j <= 2 && i + j < clusterNodes.length; j++) {
          this.virtualEdges.push({
            from: clusterNodes[i].id,
            to: clusterNodes[i + j].id,
            similarity: 0.5,
            source: clusterNodes[i].id,
            target: clusterNodes[i + j].id,
            isVirtual: true,
          } as D3Edge);
        }
      }
    });
  }
}

/**
 * Vue composable for using force layout
 */
export function useForceLayout() {
  const forceLayoutManager = ref<ForceLayoutManager | null>(null);
  // available strategies, the first will be the default
  const layoutStrategies: ForceLayoutStrategy[] = ['experimental', 'default'];

  /**
   * Initialize a new force layout
   */
  function initForceLayout(
    nodes: Node[],
    edges: Edge[],
    clusters: ClusterInfo[],
    options: ForceLayoutOptions,
    strategy: ForceLayoutStrategy = 'default',
  ): Simulation<D3Node, D3Edge> {
    // Clean up any existing simulation
    if (forceLayoutManager.value) {
      forceLayoutManager.value.destroySimulation();
    }

    // Create new manager
    forceLayoutManager.value = new ForceLayoutManager(
      nodes,
      edges,
      clusters,
      options,
    );
    forceLayoutManager.value.setStrategy(strategy);

    // Initialize simulation
    return forceLayoutManager.value.initSimulation();
  }

  /**
   * Clean up resources
   */
  function destroyForceLayout(): void {
    if (forceLayoutManager.value) {
      forceLayoutManager.value.destroySimulation();
      forceLayoutManager.value = null;
    }
  }

  return {
    initForceLayout,
    destroyForceLayout,
    forceLayoutManager,
    layoutStrategies,
  };
}
