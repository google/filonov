<template>
  <q-dialog v-model="isOpen" position="top">
    <q-card style="width: 600px; max-width: 80vw">
      <q-card-section class="q-pa-sm">
        <q-input
          v-model="searchQuery"
          dense
          placeholder="Search nodes..."
          outlined
          class="no-border-radius"
          autofocus
          @keyup.esc="close"
          @keyup.down.prevent="moveSelection(1)"
          @keyup.up.prevent="moveSelection(-1)"
          @keyup.enter="selectCurrent"
        >
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </q-card-section>

      <q-card-section class="scroll q-pa-none" style="max-height: 300px">
        <q-list padding ref="listRef" class="scroll">
          <q-item
            v-for="(node, index) in filteredNodes"
            :key="node.id"
            clickable
            v-ripple
            @click="selectNode(node)"
            :active="selectedIndex === index"
            :class="{ 'bg-blue-1': index === selectedIndex }"
          >
            <q-item-section>
              <q-item-label>{{ node.label }}</q-item-label>
              <q-item-label caption>ID: {{ node.id }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="filteredNodes.length === 0 && searchQuery">
            <q-item-section>
              <q-item-label class="text-grey">No matches found</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import { Node } from 'components/models';
import { QList } from 'quasar';

const props = defineProps<{
  nodes: Node[];
}>();

const emit = defineEmits<{
  (e: 'node-selected', node: Node): void;
  (e: 'update:modelValue', value: boolean): void;
}>();

const isOpen = ref(false);
const searchQuery = ref('');
const selectedIndex = ref(0);
const listRef = ref<InstanceType<typeof QList> | null>(null);

const filteredNodes = computed(() => {
  if (!searchQuery.value) return [];

  const query = searchQuery.value.toLowerCase();
  return props.nodes.filter(
    (node) =>
      node.label?.toLowerCase().includes(query) ||
      node.id.toString().toLowerCase().includes(query) ||
      node.name?.toLocaleLowerCase().includes(query),
  );
});

watch(searchQuery, () => {
  selectedIndex.value = 0;
});

function moveSelection(delta: number) {
  const newIndex = selectedIndex.value + delta;
  if (newIndex >= 0 && newIndex < filteredNodes.value.length) {
    selectedIndex.value = newIndex;
    // Scroll selected item into view
    nextTick(() => {
      const items = listRef.value?.$el.getElementsByClassName('q-item');
      if (items && items[selectedIndex.value]) {
        const item = items[selectedIndex.value] as HTMLElement;
        item.scrollIntoView({ block: 'nearest' });
      }
    });
  }
}

function selectCurrent() {
  if (filteredNodes.value.length > 0) {
    selectNode(filteredNodes.value[selectedIndex.value]);
  }
}

function selectNode(node: Node) {
  emit('node-selected', node);
  close();
}

function close() {
  isOpen.value = false;
  emit('update:modelValue', false);
  searchQuery.value = '';
  selectedIndex.value = 0;
}

function open() {
  isOpen.value = true;
}

defineExpose({
  open,
});
</script>

<style lang="scss" scoped>
.no-border-radius {
  border-radius: 8px;
}

:deep(.q-dialog__inner) {
  margin-top: 80px;
}

.q-card {
  border-radius: 12px;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.9);
}
</style>
