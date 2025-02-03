<template>
  <q-page class="full-height">
    <Suspense>
      <template #default>
        <MainComponent />
      </template>
      <template #fallback>
        <div class="row items-center justify-center">
          <span>Loading...</span>
        </div>
      </template>
    </Suspense>
  </q-page>
</template>

<script setup lang="ts">
//import { ref } from 'vue';
import MainComponent from 'components/MainComponent.vue';

defineOptions({
  name: 'IndexPage',
});
</script>
