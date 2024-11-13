import { ref } from 'vue';
import { defineStore } from 'pinia';
import { Node, Edge } from 'components/models';

export const useGraphStore = defineStore('graph', () => {
  const nodes = ref([] as Node[]);
  const edges = ref([] as Edge[]);

  // function loadGraph() {

  // }

  return {
    nodes,
    edges,
  };
});
