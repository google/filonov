
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
