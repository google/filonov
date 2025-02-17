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
export function initClusters(nodes: Node[], edges: Edge[]): ClusterInfo[] {
  const clusters = [] as ClusterInfo[];
  const visited = new Set();

  // Find all clusters
  let clusterId = 0;
  nodes.forEach((node) => {
    if (!visited.has(node.id.toString())) {
      clusterId++;
      const clusterNodes = findConnectedNodes(node, nodes, edges);
      clusterNodes.forEach((n) => visited.add(n.id.toString()));
      clusterNodes.forEach((n) => (n.cluster = clusterId.toString()));
      const metrics = aggregateNodesMetrics(clusterNodes);
      clusters.push({
        id: clusterId.toString(),
        nodes: clusterNodes,
        metrics,
      });
    }
  });
  return clusters;
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
    if (sampleNode.info['clicks'] && sampleNode.info['impressions']) {
      // ctr
      let clicks = 0;
      let impressions = 0;
      nodes.map((n) => {
        if (
          n.info &&
          n.info['clicks'] !== undefined &&
          n.info['impressions'] !== undefined
        ) {
          clicks += Number(n.info['clicks']);
          impressions += Number(n.info['impressions']);
          n.info['ctr'] =
            Number(n.info['clicks']) / Number(n.info['impressions']);
          if (n.series) {
            Object.values(n.series).forEach((item) => {
              item['ctr'] =
                Number(item['clicks']) / Number(item['impressions']);
            });
          }
        }
      });
      metrics['ctr'] = clicks / impressions;
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
