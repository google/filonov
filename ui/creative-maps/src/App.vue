<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';

const $q = useQuasar();

defineOptions({
  name: 'App',
});

// Load preference on component mount
onMounted(() => {
  const darkModePreference = localStorage.getItem('darkMode');
  if (darkModePreference !== null) {
    $q.dark.set(darkModePreference === 'true');
  }
});

// Save preference whenever it changes
watch(
  () => $q.dark.isActive,
  (isDark) => {
    localStorage.setItem('darkMode', isDark.toString());
  },
);
</script>
