<template>
  <div class="cluster-histogram">
    <svg ref="svgRef" width="100%" :height="height"></svg>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'MetricHistogram',
  props: {
    data: {
      type: Array,
      //required: true,
    },
    metric: {
      type: String,
      required: true,
    },
    height: {
      type: Number,
      default: 100,
    },
    showTitle: {
      type: Boolean,
      default: false,
    },
  },
  mounted() {
    try {
      this.drawHistogram();
    } catch (e) {
      console.error(e);
    }
  },
  watch: {
    data: {
      deep: true,
      handler() {
        this.drawHistogram();
      },
    },
  },
  computed: {
    totalHeight() {
      return this.height + 30;
    },
  },
  methods: {
    drawHistogram() {
      if (!this.$refs.svgRef) {
        console.log('empty this.$refs.svgRef');
        return;
      }
      const svg = d3.select(this.$refs.svgRef);
      svg.selectAll('*').remove();

      if (!this.data || this.data.length === 0) return;

      const margin = { top: 10, right: 10, bottom: 20, left: 30 };
      const width = this.$refs.svgRef.clientWidth;
      const height = this.height;
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;

      const x = d3
        .scaleLinear()
        .domain([
          d3.min(this.data, (d) => d.x0),
          d3.max(this.data, (d) => d.x1),
        ])
        .range([0, innerWidth]);

      const y = d3
        .scaleLinear()
        .domain([0, d3.max(this.data, (d) => d.count)])
        .range([innerHeight, 0]);

      const g = svg
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Add bars
      g.selectAll('rect')
        .data(this.data)
        .join('rect')
        .attr('x', (d) => x(d.x0))
        .attr('y', (d) => y(d.count))
        .attr('width', (d) => Math.max(1, x(d.x1) - x(d.x0) - 1))
        .attr('height', (d) => Math.max(1, innerHeight - y(d.count)))
        .attr('fill', '#69b3a2')
        .attr('opacity', 0.8)
        .attr('cursor', 'pointer') // Show pointer cursor
        .on('click', (event, d) => {
          this.$emit('metric-clicked', { metric: this.metric, nodes: d.nodes });
        })
        .on('mouseover', (event, d) => {
          const tooltip = d3
            .select(this.$el)
            .select('.tooltip')
            .style('opacity', 1)
            .style('left', `${event.offsetX + 10}px`)
            .style('top', `${event.offsetY - 10}px`);
          tooltip.html(`${d.x0.toFixed(1)}-${d.x1.toFixed(1)}: ${d.count}`);
        })
        .on('mouseout', () => {
          d3.select(this.$el).select('.tooltip').style('opacity', 0);
        });

      // Add tooltip div if not exists
      if (!d3.select(this.$el).select('.tooltip').size()) {
        d3.select(this.$el)
          .append('div')
          .attr('class', 'tooltip')
          .style('opacity', 0);
      }

      // Add axes
      g.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(5));

      g.append('g').call(d3.axisLeft(y).ticks(5));

      // // Add metric name as title
      if (this.showTitle) {
        g.append('text')
          .attr('class', 'metric-name')
          .attr('x', innerWidth / 2)
          .attr('y', -margin.top / 2)
          .attr('text-anchor', 'middle')
          .style('font-size', '12px')
          .text(this.metric);
      }
    },
  },
};
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
