<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated :class="$q.dark.isActive ? 'bg-deep-purple-10' : 'bg-primary'">
      <q-toolbar>
        <q-toolbar-title class="flex items-center"
          ><Logo :size="40" class="q-mr-sm" />Filonov (a.k.a Creative Maps)
        </q-toolbar-title>
        <q-btn
          :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
          flat
          round
          @click="$q.dark.toggle()"
          aria-label="Toggle dark mode"
        />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
    <q-footer
      :class="$q.dark.isActive ? 'bg-grey-9 text-white' : 'bg-white text-dark'"
    >
      <div class="text-body1 text-center q-ma-sm">
        &copy;&nbsp;Google gTech Ads, 2025. Built
        {{ formattedBuildTime }} (git#{{ GIT_HASH }}) (not an official Google
        product)
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
