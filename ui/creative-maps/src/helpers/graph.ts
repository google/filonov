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
