<template>
  <q-card style="width: 300px">
    <q-card-section>
      <div class="absolute-top-right">
        <q-btn flat round dense icon="close" @click="$emit('remove')" />
      </div>
      <div class="text-h6">
        <a
          href="#"
          class="text-primary"
          @click.prevent="$emit('click', clusterId)"
        >
          Cluster {{ clusterId }}
        </a>
      </div>

      <!-- Basic Stats -->
      <div class="text-subtitle2 q-mt-md">Basic Statistics</div>
      <div class="q-pl-sm">
        <div>Nodes: {{ nodes.length }}</div>
        <!-- <div>Connected components: {{ getConnectedComponentsCount() }}</div> -->
      </div>

      <!-- Aggregated Metrics -->
      <div class="text-subtitle2 q-mt-md">Average Metrics</div>
      <div class="q-pl-sm">
        <div
          v-for="(value, metric) in averageMetrics"
          :key="metric"
          class="q-mb-xs"
        >
          <strong>{{ metric }}:</strong> {{ formatMetricValue(value, metric) }}
        </div>
      </div>

      <!-- Top Tags -->
      <div class="text-subtitle2 q-mt-md">Top Tags</div>
      <div class="row q-gutter-xs q-mt-sm">
        <q-chip v-for="tag in topTags" :key="tag.tag" size="sm" outline>
          {{ tag.tag }} ({{ tag.freq }})
        </q-chip>
      </div>

      <!-- Value Ranges -->
      <div class="text-subtitle2 q-mt-md">Metric Ranges</div>
      <div class="q-pl-sm">
        <div
          v-for="(range, metric) in metricRanges"
          :key="metric"
          class="q-mb-xs"
        >
          <strong>{{ metric }}:</strong>
          {{ formatMetricValue(range.min, metric) }} -
          {{ formatMetricValue(range.max, metric) }}
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script lang="ts">
import { defineComponent, PropType, computed } from 'vue';
import { Node } from 'components/models';
import { aggregateNodesMetrics, formatMetricValue } from 'src/helpers/utils';

export default defineComponent({
  name: 'ClusterCard',
  props: {
    clusterId: {
      type: String,
      required: true,
    },
    nodes: {
      type: Array as PropType<Node[]>,
      required: true,
    },
  },
  emits: ['remove', 'click'],
  setup(props) {
    const averageMetrics = computed(() => {
      return aggregateNodesMetrics(props.nodes);
    });

    const metricRanges = computed(() => {
      const ranges: Record<string, { min: number; max: number }> = {};
      if (!props.nodes.length || !props.nodes[0].info) return ranges;

      Object.keys(props.nodes[0].info).forEach((metric) => {
        const values = props.nodes
          .map((node) => node.info?.[metric] as number)
          .filter((v) => v !== undefined && v !== null);

        if (values.length) {
          ranges[metric] = {
            min: Math.min(...values),
            max: Math.max(...values),
          };
        }
      });

      return ranges;
    });

    const topTags = computed(() => {
      const tagCounts = new Map<string, number>();

      props.nodes.forEach((node) => {
        node.tags?.forEach((tagInfo) => {
          tagCounts.set(tagInfo.tag, (tagCounts.get(tagInfo.tag) || 0) + 1);
        });
      });

      return Array.from(tagCounts.entries())
        .map(([tag, freq]) => ({ tag, freq }))
        .sort((a, b) => b.freq - a.freq)
        .slice(0, 5); // Show top 5 tags
    });

    const getConnectedComponentsCount = () => {
      return 1;
    };

    return {
      averageMetrics,
      metricRanges,
      topTags,
      getConnectedComponentsCount,
      formatMetricValue,
    };
  },
});
</script>
