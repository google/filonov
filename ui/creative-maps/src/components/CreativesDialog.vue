<template>
  <q-dialog v-model="showDialog" maximized>
    <q-card class="full-width">
      <q-card-section class="row items-center">
        <div class="text-h6">Creatives</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-table
          :rows="nodes"
          :columns="columns"
          row-key="id"
          :pagination="{ rowsPerPage: 15 }"
        >
          <template #top-right>
            <q-btn-dropdown color="primary" label="Export">
              <q-list>
                <q-item clickable v-close-popup @click="exportAs('csv')">
                  <q-item-section>
                    <q-item-label>as CSV</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="exportAs('json')">
                  <q-item-section>
                    <q-item-label>as JSON</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </template>

          <template #body-cell-media_path="props">
            <q-td :props="props">
              <a :href="props.value" target="_blank">{{ props.value }}</a>
            </q-td>
          </template>
        </q-table>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { QTableColumn, exportFile } from 'quasar';
import { Node } from './models';
import { exportTable } from 'src/helpers/export';

interface Props {
  nodes: Node[];
  modelValue: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue']);

const showDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const columns: QTableColumn[] = [
  {
    name: 'label',
    required: true,
    label: 'Label',
    align: 'left',
    field: 'label',
    sortable: true,
  },
  {
    name: 'media_path',
    align: 'left',
    label: 'Media Path',
    field: 'media_path',
    sortable: true,
  },
];

function exportAs(format: 'csv' | 'json') {
  const data = props.nodes.map((node) => ({
    name: node.name,
    media_path: node.media_path,
  }));

  if (format === 'csv') {
    const csvColumns: QTableColumn[] = [
      { name: 'name', label: 'Name', field: 'name' },
      { name: 'media_path', label: 'Media Path', field: 'media_path' },
    ];
    exportTable(csvColumns, data, 'creatives');
  } else if (format === 'json') {
    const status = exportFile(
      'creatives.json',
      JSON.stringify(data, null, 2),
      'application/json',
    );
    if (!status) {
      console.error('Browser denied file download');
    }
  }
}
</script>
