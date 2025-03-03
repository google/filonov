import { isNumber, isString } from 'lodash';
import { ClusterInfo, Edge, MetricsObject, Node } from 'src/components/models';

/**
 * Sort tags in nodes in order of score decreasing.
 * @param nodes all graph node
 */
export function sortTags(nodes: Node[]) {
  nodes.forEach((node) => {
    if (!node.tags) {
      node.tags = [];
    } else {
      node.tags.sort((a, b) => b.score - a.score);
    }
  });
}

/**
 * Group connected nodes in clusters and calculate aggregated metrics for clusters.
 * @param nodes all graph nodes
 * @param edges all graph edges (links)
 * @return array of clusters
 */
export function initClusters(
  nodes: Node[],
  edges: Edge[],
  sortBy: string,
): ClusterInfo[] {
  const clusters = [] as ClusterInfo[];
  const visited = new Set();

  // Find all clusters
  nodes.forEach((node) => {
    if (!visited.has(node.id.toString())) {
      const clusterNodes = findConnectedNodes(node, nodes, edges);
      clusterNodes.forEach((n) => visited.add(n.id.toString()));
      const metrics = aggregateNodesMetrics(clusterNodes);
      clusters.push({
        id: '',
        nodes: clusterNodes,
        metrics,
      });
    }
  });
  if (sortBy) {
    if (clusters.every((c) => isNumber(c.metrics[sortBy]))) {
      clusters.sort((a, b) => {
        return (
          ((b.metrics['cost'] as number) || 0) -
          ((a.metrics['cost'] as number) || 0)
        );
      });
    } else {
      clusters.sort((a, b) => {
        return b.nodes.length - a.nodes.length;
      });
    }
  }
  clusters.forEach((cluster, index) => {
    const clusterId = (index + 1).toString();
    cluster.id = clusterId;
    cluster.nodes.forEach((n) => (n.cluster = clusterId));
  });
  return clusters;
}

export function optimizeGraphEdges(
  nodes: Node[],
  edges: Edge[],
  keepTopPercentage = 0.2,
) {
  // Group nodes by cluster
  const clusterMap = new Map<string, Node[]>();

  nodes.forEach((node) => {
    if (!clusterMap.has(node.cluster)) {
      clusterMap.set(node.cluster, []);
    }
    clusterMap.get(node.cluster)!.push(node);
  });

  // Group edges by cluster
  const clusterEdges = new Map<string, Edge[]>();

  edges.forEach((edge) => {
    const sourceNode = nodes.find((n) => n.id === edge.from);
    const targetNode = nodes.find((n) => n.id === edge.to);

    if (sourceNode && targetNode && sourceNode.cluster === targetNode.cluster) {
      const cluster = sourceNode.cluster;
      if (!clusterEdges.has(cluster)) {
        clusterEdges.set(cluster, []);
      }
      clusterEdges.get(cluster)!.push(edge);
    }
  });

  // Create a minimum spanning tree for each cluster
  let optimizedEdges: Edge[] = [];

  clusterMap.forEach((clusterNodes, clusterId) => {
    const clusterEdgeList = clusterEdges.get(clusterId) || [];

    // Create MST for this cluster
    const mstEdges = createMinimumSpanningTree(clusterNodes, clusterEdgeList);

    // If we want to keep some additional high-similarity edges
    if (keepTopPercentage > 0 && keepTopPercentage < 1) {
      // Sort non-MST edges by similarity
      const mstEdgeSet = new Set(mstEdges.map((e) => `${e.from}-${e.to}`));
      const nonMstEdges = clusterEdgeList
        .filter(
          (e) =>
            !mstEdgeSet.has(`${e.from}-${e.to}`) &&
            !mstEdgeSet.has(`${e.to}-${e.from}`),
        )
        .sort((a, b) => b.similarity - a.similarity);

      // Keep top percentage of non-MST edges
      const additionalEdgesToKeep = Math.floor(
        nonMstEdges.length * keepTopPercentage,
      );
      const highSimilarityEdges = nonMstEdges.slice(0, additionalEdgesToKeep);

      // Add both MST and high similarity edges
      optimizedEdges = [...optimizedEdges, ...mstEdges, ...highSimilarityEdges];
    } else {
      // Just add MST edges
      optimizedEdges = [...optimizedEdges, ...mstEdges];
    }
  });

  return optimizedEdges;
}

/**
 * This function creates a minimum spanning tree from a given set of nodes and edges
 * to reduce the number of edges while maintaining connectivity.
 * It uses Kruskal's algorithm to find the minimum spanning tree.
 */
export function createMinimumSpanningTree(
  nodes: Node[],
  edges: Edge[],
): Edge[] {
  // Create a disjoint-set data structure for union-find operations
  const disjointSet = new Map<number, number>();

  // Initialize each node as its own set
  nodes.forEach((node) => {
    disjointSet.set(node.id, node.id);
  });

  // Find function for the disjoint-set
  const find = (nodeId: number): number => {
    if (disjointSet.get(nodeId) !== nodeId) {
      disjointSet.set(nodeId, find(disjointSet.get(nodeId)!));
    }
    return disjointSet.get(nodeId)!;
  };

  // Union function for the disjoint-set
  const union = (nodeId1: number, nodeId2: number): void => {
    const root1 = find(nodeId1);
    const root2 = find(nodeId2);
    if (root1 !== root2) {
      disjointSet.set(root2, root1);
    }
  };

  // Sort edges by similarity (descending order since higher similarity is better)
  const sortedEdges = [...edges].sort((a, b) => b.similarity - a.similarity);

  // Result array to store MST edges
  const mstEdges: Edge[] = [];

  // Process edges in order of decreasing similarity
  for (const edge of sortedEdges) {
    const fromRoot = find(edge.from);
    const toRoot = find(edge.to);

    // If including this edge doesn't create a cycle, add it to the MST
    if (fromRoot !== toRoot) {
      mstEdges.push(edge);
      union(fromRoot, toRoot);
    }
  }

  return mstEdges;
}

/**
 * Return all connected nodes (directly or indirectly) for a given node.
 * @param startNode A node to start with.
 * @param nodes All nodes to analyze.
 * @param edges All edges between nodes.
 * @return list of connected nodes
 */
export function findConnectedNodes(
  startNode: Node,
  nodes: Node[],
  edges: Edge[],
): Node[] {
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

    const neighbors = adjacencyMap.get(currentId);
    if (neighbors) {
      for (const neighborId of neighbors) {
        if (!visited.has(neighborId)) {
          queue.push(neighborId);
        }
      }
    }
  }

  return nodes.filter((n) => connected.has(n.id.toString()));
}

/**
 * Aggregate nodes metrics.
 * At the moment all numeric metrics are summed up.
 * @param nodes Nodes
 * @return Aggregated nodes metrics
 */
export function aggregateNodesMetrics(nodes: Node[]): MetricsObject {
  if (!nodes || nodes.length === 0) return {};
  const sampleNode = nodes.find((n) => n.info);
  const metrics: Record<string, number | string> = {};
  if (sampleNode && sampleNode.info) {
    Object.entries(sampleNode.info).forEach(([key, value]) => {
      if (isNumber(value)) {
        const values = (nodes.map((n) => n.info?.[key]) as number[]).filter(
          (v) => isNumber(v),
        );

        if (values.length > 0) {
          metrics[key] = aggregateMetric(key, values);
        }
      } else if (isString(value)) {
        const valueCounts = (nodes.map((n) => n.info?.[key]) as string[])
          .filter((v) => v !== undefined)
          .reduce((acc: Record<string, number>, val: string) => {
            acc[val] = ((acc[val] as number) || 0) + 1;
            return acc;
          }, {});

        const mostCommon = Object.entries(valueCounts).sort(
          (a, b) => b[1] - a[1],
        )[0];

        if (mostCommon) {
          metrics[key] =
            mostCommon[0] + ' (' + mostCommon[1] + '/' + nodes.length + ')';
        }
      }
    });
    // calculate some computed metrics
    if (sampleNode.info) {
      // CTR - clicks / impressions
      // CR - conversions / clicks
      // CPA - cost / conversions
      // ROAS - conversions_value / cost
      // CPM - (cost / impressions) * 1000
      let clicks = 0;
      let impressions = 0;
      let conversions = 0;
      let cost = 0;
      let conversions_value = 0;
      nodes.forEach((n) => {
        if (!n.info) return;
        if (n.info['clicks'] !== undefined) {
          clicks += Number(n.info['clicks']);
        }
        if (n.info['impressions'] !== undefined) {
          impressions += Number(n.info['impressions']);
        }
        if (n.info['conversions'] !== undefined) {
          conversions += Number(n.info['conversions']);
        }
        if (n.info['cost'] !== undefined) {
          cost += Number(n.info['cost']);
        }
        if (n.info['conversions_value'] !== undefined) {
          conversions_value += Number(n.info['conversions_value']);
        }
        // CTR - clicks / impressions
        if (
          n.info['clicks'] !== undefined &&
          n.info['impressions'] !== undefined
        ) {
          n.info['ctr'] =
            Number(n.info['clicks']) / Number(n.info['impressions']);
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['ctr'] =
                Number(item['clicks']) / Number(item['impressions']);
            });
          }
        }
        // CR - conversions / clicks
        if (
          n.info['conversions'] !== undefined &&
          n.info['clicks'] !== undefined
        ) {
          n.info['cr'] =
            Number(n.info['conversions']) / Number(n.info['clicks']);
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['cr'] = Number(item['conversions']) / Number(item['clicks']);
            });
          }
        }
        // CPA - cost / conversions
        if (
          n.info['cost'] !== undefined &&
          n.info['conversions'] !== undefined
        ) {
          n.info['cpa'] =
            Number(n.info['cost']) / Number(n.info['conversions']);
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['cpa'] = Number(item['cost']) / Number(item['conversions']);
            });
          }
        }
        // ROAS - conversions_value / cost
        if (
          n.info['conversions_value'] !== undefined &&
          n.info['cost'] !== undefined
        ) {
          n.info['roas'] =
            Number(n.info['conversions_value']) / Number(n.info['cost']);
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['roas'] =
                Number(item['conversions_value']) / Number(item['cost']);
            });
          }
        }
        // CPM - (cost / impressions) * 1000
        if (
          n.info['cost'] !== undefined &&
          n.info['impressions'] !== undefined
        ) {
          n.info['cpm'] =
            (Number(n.info['cost']) / Number(n.info['impressions'])) * 1000;
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['cpm'] =
                (Number(item['cost']) / Number(item['impressions'])) * 1000;
            });
          }
        }
      });
      metrics['ctr'] = clicks / impressions;
      metrics['cr'] = conversions / clicks;
      metrics['cpa'] = cost / conversions;
      metrics['roas'] = conversions_value / cost;
      metrics['cpm'] = (cost / impressions) * 1000;
    }
  }
  return metrics;
}

/**
 * Calculate an aggregated metric value.
 * @param name A metric name.
 * @param values Many values of the metric.
 * @return Aggregated metric value
 */
function aggregateMetric(name: string, values: number[]) {
  // TODO: probably the aggregate method should be different for different metrics.
  // sum:
  return values.reduce((sum, val) => sum + val, 0);
  // arv:
  // values.reduce((sum, val) => sum + val, 0) / values.length;
}

export const computedMetrics = ['ctr', 'cr', 'cpa', 'roas', 'cpm'];

export function getTotalsRow(nodes: MetricsObject[], metrics: string[]) {
  const totals: Record<string, number> = {};

  metrics.forEach((metric) => {
    if (computedMetrics.includes(metric)) {
      // For computed metrics, we'll recalculate them based on totals
      return;
    }

    const values = nodes
      .map((node) => node[metric])
      .filter((v) => isNumber(v)) as number[];

    if (values.length > 0) {
      totals[metric] = values.reduce((sum, val) => sum + (val as number), 0);
    }
  });

  // Calculate computed metrics based on aggregated values
  if (
    isNumber(totals['clicks']) &&
    isNumber(totals['impressions']) &&
    (totals['impressions'] as number) > 0
  ) {
    totals['ctr'] =
      (totals['clicks'] as number) / (totals['impressions'] as number);
  }

  if (
    isNumber(totals['conversions']) &&
    isNumber(totals['clicks']) &&
    (totals['clicks'] as number) > 0
  ) {
    totals['cr'] =
      (totals['conversions'] as number) / (totals['clicks'] as number);
  }

  if (
    isNumber(totals['cost']) &&
    isNumber(totals['conversions']) &&
    (totals['conversions'] as number) > 0
  ) {
    totals['cpa'] =
      (totals['cost'] as number) / (totals['conversions'] as number);
  }

  if (
    isNumber(totals['conversions_value']) &&
    isNumber(totals['cost']) &&
    (totals['cost'] as number) > 0
  ) {
    totals['roas'] =
      (totals['conversions_value'] as number) / (totals['cost'] as number);
  }

  if (
    isNumber(totals['cost']) &&
    isNumber(totals['impressions']) &&
    (totals['impressions'] as number) > 0
  ) {
    totals['cpm'] =
      ((totals['cost'] as number) / (totals['impressions'] as number)) * 1000;
  }

  return totals;
}

/**
 * Format arbitrary metric's value.
 * @param value A value
 * @param metric A metric name
 * @return a formatted string value
 */
export function formatMetricValue(
  value: number | string | boolean | undefined,
  metric: string,
) {
  if (typeof value !== 'number') return value;

  if (
    metric === 'impressions' ||
    metric === 'clicks' ||
    metric === 'cost' ||
    metric === 'inapps'
  ) {
    return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  if (metric === 'duration') {
    return `${(value / 60).toFixed(1)} min`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function formatMetricWithProportion(
  value: number | string,
  metric: string,
  totals: Record<string, number | string>,
): string | undefined {
  if (!isNumber(value)) return value as string;

  const numValue = value as number;
  const formattedValue = formatMetricValue(numValue, metric);

  if (computedMetrics.includes(metric)) {
    return formatMetricValue(value, metric) as string;
  }

  const total = totals[metric];
  if (total && isNumber(total) && total !== 0) {
    const proportion = (numValue / total) * 100;
    return `${formattedValue} (${proportion.toFixed(1)}%)`;
  }

  return formattedValue as string;
}
