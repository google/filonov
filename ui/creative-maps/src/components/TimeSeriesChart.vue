<template>
  <div class="time-series-chart">
    <div class="row items-center q-mb-md">
      <q-select
        v-model="selectedNodes"
        :options="availableNodes"
        multiple
        use-chips
        :label="`Add node's ${metric} values`"
        class="col-grow"
        emit-value
        map-options
        option-label="label"
        option-value="id"
      />
    </div>
    <apexchart
      type="line"
      :options="chartOptions"
      :series="series"
      :height="height"
    />
    <div class="row q-gutter-md q-mt-lg">
      <node-card
        v-for="nodeId in selectedNodes"
        :key="nodeId"
        :node="getNode(nodeId)"
        @remove="removeNode(nodeId)"
        style="width: 300px"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from 'vue';
import { ApexOptions } from 'apexcharts';
import { ComputedRef } from 'vue';
import { Node } from 'components/models';
import { formatMetricValue } from 'src/helpers/utils';
import NodeCard from './NodeCard.vue';

export default defineComponent({
  name: 'TimeSeriesChart',
  props: {
    data: {
      type: Array<{ date: Date; value: number }>,
      required: true,
    },
    metric: {
      type: String,
      required: true,
    },
    height: {
      type: Number,
      default: 300,
    },
    clusterNodes: {
      type: Array<Node>,
      required: true,
    },
  },
  components: { NodeCard },
  setup(props) {
    const selectedNodes = ref([]);

    const availableNodes = computed(() =>
      props.clusterNodes.map((node: Node) => ({
        label: node.label + ' (' + node.name + ')',
        id: node.id,
        series: node.series,
      })),
    );

    const series = computed(() => {
      // Start with cluster average series
      const allSeries = [
        {
          name: 'Cluster',
          data: props.data.map((d) => ({
            x: d.date,
            y: d.value,
          })),
        },
      ];

      // Add selected nodes series
      selectedNodes.value.forEach((nodeId) => {
        const node = props.clusterNodes.find((n) => n.id === nodeId);
        if (node?.series) {
          allSeries.push({
            name: `Node ${nodeId}`,
            data: Object.entries(node.series).map(([date, metrics]) => ({
              x: new Date(date),
              y: metrics[props.metric] as number,
            })),
          });
        }
      });

      return allSeries;
    });

    const chartOptions: ComputedRef<ApexOptions> = computed(() => ({
      chart: {
        type: 'line',
        zoom: {
          enabled: true,
        },
      },
      markers: {
        size: 4,
        hover: {
          size: 6,
        },
      },
      stroke: {
        curve: 'smooth',
        width: 2,
      },
      tooltip: {
        x: {
          format: 'yyyy-MM-dd',
        },
        y: {
          formatter: (value) => value.toFixed(2),
        },
      },
      xaxis: {
        type: 'datetime',
        title: {
          text: 'Date',
        },
      },
      yaxis: {
        title: {
          text: props.metric,
        },
        labels: {
          formatter: (val) => val.toFixed(2),
        },
      },
    }));

    const getNode = (nodeId: number) =>
      props.clusterNodes.find((node) => node.id === nodeId)!;

    const removeNode = (nodeId: number) => {
      selectedNodes.value = selectedNodes.value.filter((id) => id !== nodeId);
    };

    return {
      series,
      chartOptions,
      selectedNodes,
      availableNodes,
      getNode,
      removeNode,
      formatMetricValue,
    };
  },
});
</script>

<style scoped>
.time-series-chart {
  width: 100%;
  background: white;
}
</style>
