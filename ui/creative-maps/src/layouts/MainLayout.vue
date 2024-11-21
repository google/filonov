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

    <div class="text-body1 text-center q-ma-sm">
      &copy;&nbsp;Google gTech Ads, 2024.
    </div>
  </q-layout>
</template>

<script setup lang="ts">
import Logo from 'components/Logo.vue';

defineOptions({
  name: 'MainLayout',
});
</script>
