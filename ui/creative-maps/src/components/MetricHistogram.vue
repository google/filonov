<template>
  <div class="cluster-histogram" ref="rootEl">
    <svg ref="svgRef" width="100%" :height="height"></svg>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';
import { AbstractNode, HistogramData, ParetoHistogramData } from './models';

interface Props {
  data: HistogramData[] | ParetoHistogramData[];
  metric: string;
  height?: number;
  showTitle?: boolean;
  isParetoMode?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  height: 100,
  isParetoMode: false,
});

const rootEl = ref<HTMLElement | null>(null);
const svgRef = ref<SVGSVGElement | null>(null);

const emit = defineEmits<{
  (
    e: 'metric-clicked',
    args: {
      metric: string;
      nodes: AbstractNode[];
      scalar: boolean;
      range: number[] | string[];
    },
  ): void;
}>();

onMounted(() => {
  try {
    if (props.isParetoMode) {
      drawParetoHistogram();
    } else {
      drawRegularHistogram();
    }
  } catch (e) {
    console.error(e);
  }
});

watch(
  () => props.data,
  () => {
    if (props.isParetoMode) {
      drawParetoHistogram();
    } else {
      drawRegularHistogram();
    }
  },
);

function drawRegularHistogram() {
  if (!svgRef.value) {
    console.log('empty this.$refs.svgRef');
    return;
  }

  const data = props.data as HistogramData[];
  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove();

  if (!props.data || props.data.length === 0) return;

  const margin = { top: 10, right: 10, bottom: 20, left: 30 };
  const width = svgRef.value.clientWidth;
  const height = props.height;
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const isStringData = typeof data[0].x0 === 'string';

  // Create appropriate scales based on data type
  const x = isStringData
    ? d3
        .scaleBand()
        .domain(data.map((d) => d.x0 as string))
        .range([0, innerWidth])
        .padding(0.1)
    : d3
        .scaleLinear()
        .domain([
          d3.min(data, (d: HistogramData) => d.x0 as number) ?? 0,
          d3.max(data, (d: HistogramData) => d.x1) ?? 0,
        ])
        .range([0, innerWidth]);

  const y = d3
    .scaleSymlog()
    .domain([0, d3.max(data, (d: HistogramData) => d.count) ?? 0])
    .range([innerHeight, 0]);

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Add bars
  g.selectAll('rect')
    .data<HistogramData>(data)
    .join('rect')
    .attr('x', (d) =>
      isStringData
        ? ((x as d3.ScaleBand<string>)(d.x0 as string) ?? 0)
        : (x as d3.ScaleLinear<number, number>)(d.x0 as number),
    )
    .attr('y', (d) => y(d.count))
    .attr('width', (d) =>
      isStringData
        ? (x as d3.ScaleBand<string>).bandwidth()
        : Math.max(
            1,
            (x as d3.ScaleLinear<number, number>)(d.x1 as number) -
              (x as d3.ScaleLinear<number, number>)(d.x0 as number) -
              1,
          ),
    )
    .attr('height', (d) => Math.max(1, innerHeight - y(d.count)))
    .attr('fill', '#69b3a2')
    .attr('opacity', 0.8)
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      emit('metric-clicked', {
        metric: props.metric,
        nodes: d.nodes,
        scalar: isStringData,
        range: isStringData
          ? ([d.x0, d.x0] as string[])
          : ([d.x0 || 0, d.x1 || 0] as number[]),
      });
    })
    .on('mouseover', (event, d) => {
      const tooltip = d3
        .select(rootEl.value)
        .select('.tooltip')
        .style('opacity', 1)
        .style('left', `${event.offsetX + 10}px`)
        .style('top', `${event.offsetY - 10}px`);
      const tooltipText = isStringData
        ? `${d.x0}: ${d.count}`
        : `${(d.x0 as number).toFixed(1)}-${(d.x1 as number).toFixed(1)}: ${d.count}`;
      tooltip.html(tooltipText);
    })
    .on('mouseout', () => {
      d3.select(rootEl.value).select('.tooltip').style('opacity', 0);
    });

  // Add tooltip div if not exists
  if (!d3.select(rootEl.value).select('.tooltip').size()) {
    d3.select(rootEl.value)
      .append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0);
  }

  // Add axes
  g.append('g')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(
      isStringData
        ? d3.axisBottom(x as d3.ScaleBand<string>).tickSizeOuter(0)
        : d3.axisBottom(x as d3.ScaleLinear<number, number>).ticks(5),
    )
    .selectAll('text')
    .style('text-anchor', 'end');

  g.append('g').call(d3.axisLeft(y).ticks(5));

  // // Add metric name as title
  if (props.showTitle) {
    g.append('text')
      .attr('class', 'metric-name')
      .attr('x', innerWidth / 2)
      .attr('y', -margin.top / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .text(props.metric);
  }
}

function drawParetoHistogram() {
  if (!svgRef.value) {
    console.log('empty this.$refs.svgRef');
    return;
  }

  const svg = d3.select(svgRef.value);
  svg.selectAll('*').remove();

  if (!props.data || props.data.length === 0) return;

  const paretoData = props.data as ParetoHistogramData[];

  const margin = { top: 10, right: 40, bottom: 20, left: 40 };
  const width = svgRef.value.clientWidth;
  const height = props.height;
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);

  // Create scales
  const x = d3.scaleLinear().domain([0, 100]).range([0, innerWidth]);

  const y = d3.scaleLinear().domain([0, 100]).range([innerHeight, 0]);

  const blueColors = [
    '#deebf7',
    '#9ecae1',
    '#6baed6',
    '#4292c6',
    '#2171b5',
    '#084594',
  ];

  // Add bars
  g.selectAll('rect')
    .data(paretoData)
    .join('rect')
    .attr('x', (d, i) => (i === 0 ? 0 : x(paretoData[i - 1].nodePercentage)))
    .attr('width', (d, i) =>
      i === 0
        ? x(d.nodePercentage)
        : x(d.nodePercentage) - x(paretoData[i - 1].nodePercentage),
    )
    .attr('y', (d) => y(d.valuePercentage))
    .attr('height', (d) => innerHeight - y(d.valuePercentage))
    .attr('fill', (d, i) => blueColors[Math.min(i, blueColors.length - 1)])
    .attr('opacity', 0.9)
    .attr('cursor', 'pointer')
    .on('click', (event, d) => {
      emit('metric-clicked', {
        metric: props.metric,
        nodes: d.nodes,
        scalar: false,
        range: [d.label, `${d.valuePercentage.toFixed(1)}%`],
      });
    })
    .on('mouseover', (event, d) => {
      const tooltip = d3
        .select(rootEl.value)
        .select('.tooltip')
        .style('opacity', 1)
        .style('left', `${event.offsetX + 10}px`)
        .style('top', `${event.offsetY - 10}px`);
      const tooltipText = `${d.label} of creatives (${d.nodes.length}) contribute ${d.valuePercentage.toFixed(1)}% of total ${props.metric}`;
      tooltip.html(tooltipText);
    })
    .on('mouseout', () => {
      d3.select(rootEl.value).select('.tooltip').style('opacity', 0);
    });

  // Add tooltip div if not exists
  if (!d3.select(rootEl.value).select('.tooltip').size()) {
    d3.select(rootEl.value)
      .append('div')
      .attr('class', 'tooltip')
      .style('opacity', 0);
  }

  // Add diagonal line (perfect equality line)
  g.append('line')
    .attr('x1', 0)
    .attr('y1', innerHeight)
    .attr('x2', innerWidth)
    .attr('y2', 0)
    .attr('stroke', 'gray')
    .attr('stroke-dasharray', '3,3')
    .attr('stroke-width', 1);

  // Add axes
  g.append('g')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(
      d3
        .axisBottom(x)
        .ticks(5)
        .tickFormat((d) => `${d}%`),
    );

  g.append('g').call(
    d3
      .axisLeft(y)
      .ticks(5)
      .tickFormat((d) => `${d}%`),
  );

  // Add right Y-axis label for clarity
  g.append('g')
    .attr('transform', `translate(${innerWidth}, 0)`)
    .call(
      d3
        .axisRight(y)
        .ticks(5)
        .tickFormat((d) => `${d}%`),
    );

  // Add metric name as title
  if (props.showTitle) {
    g.append('text')
      .attr('class', 'metric-name')
      .attr('x', innerWidth / 2)
      .attr('y', -margin.top / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .text(`${props.metric} (Contribution)`);
  }
}
</script>

<style scoped>
.cluster-histogram {
  width: 100%;
  margin: 10px 0;
}
.tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
}
</style>
