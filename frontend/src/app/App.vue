<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { authStore } from '@/modules/auth/store'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import ImmersiveLayout from '../layouts/ImmersiveLayout.vue'
import SidebarLayout from '../layouts/SidebarLayout.vue'

const route = useRoute()
const isAuthenticated = computed(() => Boolean(authStore.user))
const isImmersive = computed(() => Boolean(route.meta.immersive))

const layoutName = computed(() => {
  if (isImmersive.value) return 'immersive'
  if (isAuthenticated.value) return 'sidebar'
  return 'default'
})
</script>

<template>
  <transition name="layout" mode="out-in">
    <ImmersiveLayout v-if="layoutName === 'immersive'" :key="'layout-immersive'" />
    <SidebarLayout v-else-if="layoutName === 'sidebar'" :key="'layout-sidebar'" />
    <DefaultLayout v-else :key="'layout-default'" />
  </transition>
</template>

<style>
/* Layout-level transition - cross-fade when switching between layouts */
.layout-enter-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.layout-leave-active {
  transition: opacity 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.layout-enter-from,
.layout-leave-to {
  opacity: 0;
}
</style>
