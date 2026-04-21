<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'

import { logout, authStore } from '../stores/auth'

const router = useRouter()

const isAdmin = computed(() => authStore.user?.roles.includes('admin') ?? false)

const tabs = computed(() => {
  const items = [
    { to: '/workspace/profile', label: '个人中心' },
    { to: '/workspace/debug', label: '接口联调' },
  ]

  if (isAdmin.value) {
    items.splice(1, 0, { to: '/workspace/admin-users', label: '用户管理' })
    items.splice(2, 0, { to: '/workspace/admin-ai-configs', label: '系统配置' })
    items.splice(3, 0, { to: '/workspace/admin-emails', label: '邮件配置' })
  }

  return items
})

function handleLogout() {
  logout()
  void router.push('/auth')
}
</script>

<template>
  <main class="app-shell workspace-shell">
    <section class="workspace-frame">
      <header class="workspace-topbar panel">
        <div>
          <p class="panel-kicker">Shenlun Agent</p>
          <h1>申论训练工作台</h1>
          <p class="workspace-subtitle">当前身份：{{ isAdmin ? '管理员' : '普通用户' }}</p>
        </div>
        <div class="topbar-actions">
          <div class="topbar-user">
            <strong>{{ authStore.user?.username }}</strong>
            <span>{{ authStore.user?.email || '未填写邮箱' }}</span>
          </div>
          <button class="ghost-button" type="button" @click="handleLogout">退出登录</button>
        </div>
      </header>

      <div class="workspace-body">
        <aside class="workspace-sidebar panel">
          <nav class="route-nav">
            <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to" class="route-nav-link">
              {{ tab.label }}
            </RouterLink>
          </nav>
          <div class="workspace-meta">
            <span class="workspace-hint">系统会自动保持你的登录状态</span>
            <span class="workspace-hint">内容按页面分区，阅读更清楚</span>
            <span class="workspace-hint">适合长时间训练与查看结果</span>
          </div>
        </aside>

        <section class="workspace-content">
          <RouterView />
        </section>
      </div>
    </section>
  </main>
</template>
