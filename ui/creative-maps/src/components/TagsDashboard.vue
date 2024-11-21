<template>
  <q-card class="full-width">
    <q-card-section class="row items-center">
      <div class="text-h6">Tags Metrics Dashboard</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>
    <q-card-section class="row items-center">
      <q-btn-toggle col="col"
        v-model="isDynamicView"
        :options="[
          { label: 'Static', value: false },
          { label: 'Time Series', value: true },
        ]"
        class="q-mr-md"
      />
    </q-card-section>

    <q-card-section>
      <q-table
        v-if="!isDynamicView"
        :rows="tagsMetrics"
        :columns="columns"
        row-key="tag"
        separator="vertical"
        :pagination="{ rowsPerPage: 0 }"
      ></q-table>

      <template v-else>
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
              v-model="selectedTags"
              :options="sortedTagOptions"
              multiple
              use-chips
              label="Select tags"
            />
          </div>
        </div>

        <apexchart
          type="line"
          :options="chartOptions"
          :series="chartSeries"
          height="400"
        />
      </template>
    </q-card-section>
    <!-- <template v-slot:header="props">
      <q-tr :props="props">
        <q-th auto-width>Tag</q-th>
        <q-th auto-width>Frequency</q-th>
        <q-th v-for="metric in metrics" :key="metric" auto-width>
          {{ metric }}
        </q-th>
      </q-tr>
    </template> -->

    <!-- <template v-slot:body="props">
      <q-tr :props="props">
        <q-td auto-width>{{ props.row.tag }}</q-td>
        <q-td auto-width>{{ props.row.freq }}</q-td>
        <q-td v-for="metric in metrics" :key="metric" auto-width>
          {{ formatMetricValue(props.row.metrics[metric], metric) }}
        </q-td>
      </q-tr>
    </template> -->
  </q-card>
</template>

<script lang="ts">
import { defineComponent, ref, computed, ComputedRef, onMounted } from 'vue';
import { TagStats } from './models';
import _ from 'lodash';
import { formatMetricValue, capitalize } from 'src/helpers/utils';
import { QTableColumn } from 'quasar';

export default defineComponent({
  name: 'TagsDashboard',
  props: {
    tagsStats: {
      type: Array<TagStats>,
      required: true,
    },
  },
  setup(props) {
    const isDynamicView = ref(false);
    const selectedTags = ref<string[]>([]);
    const selectedMetric = ref('');

    const tagOptions = computed(() => props.tagsStats.map((t) => t.tag));

    const sortedTagOptions = computed(() => {
      if (!selectedMetric.value) return tagOptions.value;
      return [...props.tagsStats]
        .sort((a, b) => {
          const aValue = a.nodes.reduce(
            (sum, node) =>
              sum + ((node.info?.[selectedMetric.value] as number) || 0),
            0,
          );
          const bValue = b.nodes.reduce(
            (sum, node) =>
              sum + ((node.info?.[selectedMetric.value] as number) || 0),
            0,
          );
          return bValue - aValue;
        })
        .map((t) => t.tag);
    });

    // Get unique metrics from all nodes
    const metrics: ComputedRef<string[]> = computed(() => {
      const metricSet = new Set<string>();
      props.tagsStats.forEach((tagStat) => {
        tagStat.nodes.forEach((node) => {
          if (node.info) {
            Object.keys(node.info).forEach((metric) => metricSet.add(metric));
          }
        });
      });
      return Array.from(metricSet);
    });

    // Initialize with first metric and tag
    onMounted(() => {
      if (metrics.value.length) {
        selectedMetric.value = metrics.value[0];
      }
      if (props.tagsStats.length) {
        selectedTags.value = [props.tagsStats[0].tag];
      }
    });

    // Calculate metrics for each tag
    const tagsMetrics = computed(() => {
      return props.tagsStats.map((tagStat) => {
        const metricValues: Record<string, number> = {};
        metrics.value.forEach((metric) => {
          let isSum = true;
          if (tagStat.nodes && tagStat.nodes.length) {
            let firstNode = tagStat.nodes[0];
            if (!_.isNumber(firstNode.info?.[metric])) {
              isSum = false;
            }
          }
          if (isSum) {
            metricValues[metric] = tagStat.nodes.reduce(
              (sum, node) => sum + ((node.info?.[metric] as number) || 0),
              0,
            );
          }
        });

        return {
          tag: tagStat.tag,
          freq: tagStat.freq,
          metrics: metricValues,
        };
      });
    });

    // Define columns dynamically based on metrics
    const columns = computed<QTableColumn[]>(() => {
      const baseColumns: QTableColumn[] = [
        {
          name: 'tag',
          label: 'Tag',
          field: 'tag',
          align: 'left',
          sortable: true,
        },
        {
          name: 'freq',
          label: 'Frequency',
          field: 'freq',
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
            field: (row: any) => row.metrics[metric],
            format: (value: number) => formatMetricValue(value, metric),
            align: 'right',
            sortable: true,
            //classes: 'text-right'
          }) as QTableColumn,
      );

      return [...baseColumns, ...metricColumns];
    });

    const chartSeries = computed(() => {
      return selectedTags.value.map((tag) => {
        console.log('selected: ' + JSON.stringify(tag));
        const tagData = props.tagsStats.find((t) => t.tag === tag);
        if (!tagData) return { name: tag, data: [] };

        // Collect all dates from nodes
        const dateValues = new Map<string, number>();

        tagData.nodes.forEach((node) => {
          if (!node.series) return;

          Object.entries(node.series).forEach(([date, metrics]) => {
            const value = (metrics[selectedMetric.value] as number) || 0;
            dateValues.set(date, (dateValues.get(date) || 0) + value);
          });
        });

        // Convert to sorted array
        const data = Array.from(dateValues.entries())
          .map(([date, value]) => ({
            x: new Date(date).getTime(),
            y: value,
          }))
          .sort((a, b) => a.x - b.x);

        return {
          name: tag,
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

    return {
      isDynamicView,
      metrics,
      tagsMetrics,
      columns,
      selectedTags,
      tagOptions,
      sortedTagOptions,
      selectedMetric,
      chartSeries,
      chartOptions,
      formatMetricValue,
    };
  },
});
</script>
