<!-- TagsDashboard.vue -->
<template>
  <q-table
    :rows="tagsMetrics"
    :columns="columns"
    row-key="tag"
    separator="vertical"
    :pagination="{ rowsPerPage: 0 }"
  >
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
  </q-table>
</template>

<script lang="ts">
import { defineComponent, computed, ComputedRef } from 'vue';
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
          format: (val) => val.toLocaleString()
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

    return {
      metrics,
      tagsMetrics,
      columns,
      formatMetricValue,
    };
  },
});
</script>
