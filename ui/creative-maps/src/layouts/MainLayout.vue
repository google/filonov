<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <!-- <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        /> -->

        <q-toolbar-title class="flex items-center"
          ><Logo :size="40" class="q-mr-sm" />Filonov (a.k.a Creative Maps)
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
    <q-footer class="bg-white text-dark">
      <div class="text-body1 text-center q-ma-sm">
        &copy;&nbsp;Google gTech Ads, 2025. Built
        {{ formattedBuildTime }} (git#{{ GIT_HASH }})
      </div>
    </q-footer>
  </q-layout>
</template>

<script setup lang="ts">
import Logo from 'components/Logo.vue';

const BUILD_TIMESTAMP = process.env.BUILD_TIMESTAMP;
const GIT_HASH = process.env.GIT_HASH;

const formattedBuildTime = BUILD_TIMESTAMP
  ? new Date(BUILD_TIMESTAMP).toLocaleString()
  : '';

defineOptions({
  name: 'MainLayout',
});
</script>
