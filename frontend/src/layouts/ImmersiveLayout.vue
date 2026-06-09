<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <main class="page-main is-immersive h-screen w-full flex flex-col overflow-hidden">
    <RouterView v-slot="{ Component, route }">
      <transition name="immersive" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </RouterView>
  </main>
</template>

<style scoped>
/* Immersive transition - scale fade for full-screen pages */
.immersive-enter-active {
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.immersive-leave-active {
  transition: opacity 0.2s cubic-bezier(0.4, 0, 1, 1),
              transform 0.2s cubic-bezier(0.4, 0, 1, 1);
}

.immersive-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.immersive-leave-to {
  opacity: 0;
  transform: scale(1.01);
}
</style>
