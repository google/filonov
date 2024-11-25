<template>
  <q-card>
    <q-card-section class="row items-center">
      <div class="text-h6">Clusters Comparison</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>
    <q-card-section class="row items-center">
      <q-btn-toggle
        col="col"
        v-model="isDynamicView"
        :options="[
          { label: 'Static', value: false },
          { label: 'Time Series', value: true },
        ]"
        class="q-mr-md"
      />
    </q-card-section>
    <q-card-section>
      <template v-if="isDynamicView">
        <div class="row q-col-gutter-md q-mb-md">
          <div class="col-auto">
            <q-select
              style="min-width: 200px"
              v-model="selectedMetric"
              :options="metrics"
              label="Metric"
            />
          </div>
          <div class="col-grow">
            <q-select
              v-model="selectedClusters"
              :disable="!selectedMetric"
              :options="sortedClusterOptions"
              multiple
              use-chips
              label="Select clusters"
            />
          </div>
        </div>

        <apexchart
          type="line"
          :options="chartOptions"
          :series="chartSeries"
          height="400"
        />

        <!-- Cluster cards -->
        <div class="row q-gutter-md q-mt-lg">
          <ClusterCard
            v-for="clusterId in selectedClusters"
            :key="clusterId"
            :cluster-id="clusterId"
            :nodes="getClusterNodes(clusterId)"
            @remove="removeCluster(clusterId)"
            @click="selectCluster(clusterId)"
          />
        </div>
      </template>

      <template v-else>
        <q-table
          :rows="clustersMetrics"
          :columns="clustersListColumns"
          row-key="cluster"
          :pagination="{ rowsPerPage: 0 }"
        >
          <template #body-cell-cluster="props">
            <q-td :props="props">
              <a
                href="#"
                class="text-primary"
                @click.prevent="selectCluster(props.value)"
              >
                {{ props.value }}
              </a>
            </q-td>
          </template>
        </q-table>
      </template>
    </q-card-section>
  </q-card>
</template>

<script lang="ts">
import { defineComponent, ref, computed, ComputedRef } from 'vue';
import ClusterCard from './ClusterCard.vue';
import { Node } from './models';
import {
  aggregateNodesMetrics,
  capitalize,
  formatMetricValue,
} from 'src/helpers/utils';
import { QTableColumn } from 'quasar';
import { isNumber } from 'lodash';

export default defineComponent({
  props: {
    vertices: Array<Node>,
    clusterIds: Array<string>,
  },
  components: { ClusterCard },
  emits: ['select-cluster'],
  setup(props, { emit }) {
    const isDynamicView = ref(false);
    const selectedClusters = ref<string[]>([]);
    const selectedMetric = ref('');

    // Get all available metrics
    const metrics = computed(() => {
      const metricSet = new Set<string>();
      props.vertices?.forEach((node) => {
        if (node.info) {
          Object.keys(node.info).forEach((metric) => metricSet.add(metric));
        }
      });
      return Array.from(metricSet);
    });

    // Get clusters metrics for static view
    const clustersMetrics: ComputedRef<Record<string, number | string>[]> =
      computed(() => {
        if (!props.clusterIds) return [];
        return props.clusterIds.map((clusterId) => {
          const nodes = props.vertices!.filter((n) => n.cluster === clusterId);
          const metricValues = aggregateNodesMetrics(nodes);

          return {
            cluster: clusterId,
            size: nodes.length,
            ...metricValues,
          };
        });
      });

    // Define columns dynamically based on metrics
    const clustersListColumns = computed<QTableColumn[]>(() => {
      const baseColumns: QTableColumn[] = [
        {
          name: 'cluster',
          label: 'Cluster',
          field: 'cluster',
          align: 'left',
          sortable: true,
        },
        {
          name: 'size',
          label: 'Size',
          field: 'size',
          align: 'right',
          sortable: true,
          format: (val) => val.toLocaleString(),
        },
      ];

      // Add a column for each metric
      const metricColumns = metrics.value.map(
        (metric) =>
          ({
            name: metric,
            label: capitalize(metric),
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            field: (row: any) => row[metric],
            format: (value: number) => formatMetricValue(value, metric),
            align: 'right',
            sortable: true,
            //classes: 'text-right'
          }) as QTableColumn,
      );

      return [...baseColumns, ...metricColumns];
    });

    // Sorted cluster options for dynamic view
    const sortedClusterOptions = computed(() => {
      if (!props.clusterIds) return [];
      const metric = selectedMetric.value;
      if (!metric) return props.clusterIds;
      // return clusters ids sorted accordingly to currently selected metric
      return [...props.clusterIds].sort((a, b) => {
        const aValue =
          clustersMetrics.value.find((cm) => cm.cluster === a)?.[metric] || 0;
        const bValue =
          clustersMetrics.value.find((cm) => cm.cluster === b)?.[metric] || 0;
        if (isNumber(bValue) && isNumber(aValue)) {
          return bValue - aValue;
        } else {
          return (bValue as string).length - (aValue as string).length;
        }
      });
    });

    // Time series data for dynamic view
    const chartSeries = computed(() => {
      return selectedClusters.value.map((clusterId) => {
        const nodes = props.vertices!.filter((n) => n.cluster === clusterId);
        const dateValues = new Map<string, number>();

        nodes.forEach((node) => {
          if (!node.series) return;

          Object.entries(node.series).forEach(([date, metrics]) => {
            const value = (metrics[selectedMetric.value] as number) || 0;
            dateValues.set(date, (dateValues.get(date) || 0) + value);
          });
        });

        const data = Array.from(dateValues.entries())
          .map(([date, value]) => ({
            x: new Date(date).getTime(),
            y: value,
          }))
          .sort((a, b) => a.x - b.x);

        return {
          name: `Cluster ${clusterId}`,
          data,
        };
      });
    });

    const chartOptions = computed(() => ({
      chart: {
        type: 'line',
        zoom: { enabled: true },
      },
      xaxis: {
        type: 'datetime',
      },
      yaxis: {
        title: {
          text: selectedMetric.value,
        },
        labels: {
          formatter: (val: number) => val.toFixed(2),
        },
      },
    }));

    const getClusterNodes = (clusterId: string): Node[] => {
      if (!props.vertices) return [];
      return props.vertices.filter((node) => node.cluster === clusterId) || [];
    };

    const removeCluster = (clusterId: string) => {
      console.log('remove cluster ' + clusterId);
      selectedClusters.value = selectedClusters.value.filter(
        (id) => id !== clusterId,
      );
    };
    const selectCluster = (clusterId: string) => {
      console.log('select-cluster ' + clusterId);
      emit('select-cluster', clusterId);
    };
    return {
      selectedMetric,
      selectedClusters,
      isDynamicView,
      metrics,
      clustersMetrics,
      clustersListColumns,
      sortedClusterOptions,
      chartOptions,
      chartSeries,
      getClusterNodes,
      removeCluster,
      selectCluster,
    };
  },
});
</script>
