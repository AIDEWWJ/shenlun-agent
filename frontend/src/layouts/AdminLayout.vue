<script setup lang="ts">
/**
 * @deprecated 已废弃 — 所有认证页面统一使用 SidebarLayout
 * 保留此文件避免破坏可能的外部引用，内容与 DefaultLayout 一致
 */
import { RouterView } from 'vue-router'

import SiteFooter from '../features/navigation/components/SiteFooter.vue'
import SiteHeader from '../features/navigation/components/SiteHeader.vue'
</script>

<template>
  <div class="app-root">
    <SiteHeader />
    <main class="page-main">
      <RouterView v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </RouterView>
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-main {
  flex: 1;
}
</style>
