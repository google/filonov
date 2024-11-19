<template>
  <div class="time-series-chart">
    <svg ref="svgRef" width="100%" :height="height"></svg>
  </div>
</template>

<script>
import { defineComponent, ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';

export default defineComponent({
  name: 'TimeSeriesChart',
  props: {
    data: {
      type: Array,
      required: true
    },
    metric: {
      type: String,
      required: true
    },
    height: {
      type: Number,
      default: 300
    }
  },
  setup(props) {
    const svgRef = ref(null);
    const margin = { top: 20, right: 30, bottom: 30, left: 60 };

    const drawChart = () => {
      if (!svgRef.value || !props.data.length) return;

      const svg = d3.select(svgRef.value);
      svg.selectAll('*').remove();

      const width = svgRef.value.clientWidth - margin.left - margin.right;
      const height = props.height - margin.top - margin.bottom;

      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Create scales
      const x = d3.scaleTime()
        .domain(d3.extent(props.data, d => d.date))
        .range([0, width]);

      const y = d3.scaleLinear()
        .domain([0, d3.max(props.data, d => d.value)])
        .nice()
        .range([height, 0]);

      // Add line
      const line = d3.line()
        .x(d => x(d.date))
        .y(d => y(d.value));

      g.append('path')
        .datum(props.data)
        .attr('fill', 'none')
        .attr('stroke', 'steelblue')
        .attr('stroke-width', 1.5)
        .attr('d', line);

      // Add axes
      g.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x));

      g.append('g')
        .call(d3.axisLeft(y));

      // // Add labels
      // g.append('text')
      //   .attr('y', -margin.top/2)
      //   .attr('x', width/2)
      //   .attr('text-anchor', 'middle')
      //   .text(props.metric);
    };

    watch(() => props.data, drawChart, { deep: true });
    onMounted(drawChart);

    return {
      svgRef
    };
  }
});
</script>

<style scoped>
.time-series-chart {
  width: 100%;
  background: white;
}
</style>
