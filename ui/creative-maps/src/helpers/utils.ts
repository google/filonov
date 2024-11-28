import { Node } from 'components/models';
import { isNumber } from 'lodash';

export function assertIsError(e: unknown): asserts e is Error {
  if (!(e instanceof Error)) throw new Error('e is not an Error');
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

/**
 * Capitalize string.
 * @param str A string
 * @return
 */
export function capitalize(str: string): string {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}

function aggregateMetric(name: string, values: number[]) {
  // TODO: probably the aggregate method should be different for different metrics.
  // sum:
  return values.reduce((sum, val) => sum + val, 0);
  // arv:
  // values.reduce((sum, val) => sum + val, 0) / values.length;
}

/**
 * Aggregate nodes metrics.
 * At the moment all numeric metrics are summed up.
 * @param nodes Nodes
 * @return Aggregated nodes metrics
 */
export function aggregateNodesMetrics(nodes: Node[]) {
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
      } else if (typeof value === 'string') {
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
          metrics[key] = mostCommon[0];
        }
      }
    });
    return metrics;
  }
}
