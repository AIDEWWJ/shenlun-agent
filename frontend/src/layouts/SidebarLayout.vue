<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore, logout } from '@/modules/auth/store'
import { useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isAdmin = computed(() => authStore.user?.roles.includes('admin') ?? false)
const showDropdown = ref(false)

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

function closeDropdown() {
  showDropdown.value = false
}

function navigateTo(path: string) {
  router.push(path)
  closeDropdown()
}

function handleLogout() {
  closeDropdown()
  logout()
  void router.push('/')
}

type NavItem = { to: string; label: string; icon: 'home' | 'library' | 'history' | 'settings' | 'user' | 'lock' | 'spark' | 'admin' | 'document' | 'info' }
type NavGroup = { group: string; items: NavItem[] }

const userGroups = computed<NavGroup[]>(() => [
  {
    group: '学习',
    items: [
      { to: '/', label: '首页', icon: 'home' },
      { to: '/papers', label: '题库', icon: 'library' },
      { to: '/history', label: '练习记录', icon: 'history' },
      { to: '/error-notebook', label: '错题本', icon: 'document' },
      { to: '/study-plan', label: '学习计划', icon: 'spark' },
    ],
  },
  {
    group: '个人',
    items: [
      { to: '/profile/basic', label: '个人资料', icon: 'user' },
      { to: '/profile/security', label: '安全设置', icon: 'lock' },
      { to: '/profile/ai-config', label: 'AI 配置', icon: 'spark' },
    ],
  },
])

const adminGroups = computed<NavGroup[]>(() => [
  {
    group: '管理',
    items: [
      { to: '/admin', label: '后台总览', icon: 'admin' },
      { to: '/admin/users', label: '用户管理', icon: 'user' },
      { to: '/admin/ai-configs', label: '系统 AI 配置', icon: 'spark' },
      { to: '/admin/email', label: '邮件配置', icon: 'info' },
    ],
  },
  {
    group: '个人',
    items: [
      { to: '/profile/basic', label: '个人资料', icon: 'user' },
      { to: '/profile/security', label: '安全设置', icon: 'lock' },
      { to: '/profile/ai-config', label: 'AI 配置', icon: 'spark' },
    ],
  },
])

const groups = computed(() => isAdmin.value ? adminGroups.value : userGroups.value)

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}
</script>

<template>
  <div class="sidebar-layout">
    <!-- Sidebar -->
    <aside class="side">
      <!-- Brand -->
      <RouterLink to="/" class="side-brand">
        <span class="brand-mark">申</span>
        <span class="brand-name">申论Agent</span>
      </RouterLink>

      <!-- Nav -->
      <nav class="side-nav">
        <div v-for="g in groups" :key="g.group" class="nav-group">
          <div class="nav-group-label">{{ g.group }}</div>
          <RouterLink
            v-for="item in g.items"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            :class="{ active: isActive(item.to) }"
          >
            <AppIcon :name="item.icon" :size="16" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
      </nav>

      <!-- Bottom -->
      <div class="side-bottom">
        <span class="role-tag">
          <AppIcon name="admin" :size="12" />
          {{ authStore.user?.roles.join(' · ') || '访客' }}
        </span>
        <button type="button" class="logout-btn" @click="handleLogout">
          <AppIcon name="logout" :size="14" />
          退出
        </button>
      </div>

    </aside>

    <!-- Right area -->
    <div class="right-area">
      <!-- Top Bar -->
      <header class="top-bar">
        <div class="top-bar-right">
          <div class="user-pill" @click="toggleDropdown">
            <div class="avatar">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}</div>
            <span class="username">{{ authStore.user?.username || '用户' }}</span>
            <AppIcon name="chevron-right" :size="12" class="chevron" :class="{ open: showDropdown }" />
          </div>
        </div>

        <!-- Dropdown -->
        <transition name="dropdown">
          <div v-if="showDropdown" class="dropdown-overlay" @click="closeDropdown">
            <div class="dropdown" @click.stop>
              <div class="dropdown-user">
                <div class="dropdown-avatar">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}</div>
                <div class="dropdown-info">
                  <strong>{{ authStore.user?.username || '用户' }}</strong>
                  <span>{{ authStore.user?.email || '' }}</span>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="navigateTo('/profile/basic')">
                <AppIcon name="user" :size="14" />
                个人资料
              </button>
              <button class="dropdown-item" @click="navigateTo('/profile/security')">
                <AppIcon name="lock" :size="14" />
                安全设置
              </button>
              <div v-if="isAdmin" class="dropdown-divider"></div>
              <button v-if="isAdmin" class="dropdown-item" @click="navigateTo('/admin')">
                <AppIcon name="admin" :size="14" />
                管理后台
              </button>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item danger" @click="handleLogout">
                <AppIcon name="logout" :size="14" />
                退出登录
              </button>
            </div>
          </div>
        </transition>
      </header>

      <!-- Main -->
      <main class="side-main">
        <RouterView v-slot="{ Component, route: r }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="r.path" />
          </transition>
        </RouterView>
      </main>

      <!-- Footer -->
      <footer class="page-footer">
        <div class="footer-inner">
          <div class="footer-links">
            <a href="https://github.com/AIDEWWJ/shenlun-agent" target="_blank" rel="noopener" class="footer-link">
              <AppIcon name="github" :size="12" />
              GitHub
            </a>
          </div>
          <div class="footer-copy">© 2026 申论Agent</div>
          <div class="footer-icp">
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener" class="icp-link">
              京ICP备XXXXXXXX号
            </a>
          </div>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.sidebar-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 100vh;
  background: var(--bg);
}

/* === Sidebar === */
.side {
  background: var(--paper);
  border-right: 1px solid var(--line);
  padding: 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

/* Brand */
.side-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line-soft);
  text-decoration: none;
}

.brand-mark {
  width: 30px;
  height: 30px;
  border-radius: 7px;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 15px;
}

.brand-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
}

/* Nav */
.side-nav {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-group-label {
  padding: 14px 10px 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--support);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.nav-group-label:first-child {
  padding-top: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  color: var(--ink);
  background: var(--bg-soft);
}

.nav-item.active {
  color: var(--accent);
  background: var(--accent-soft);
  font-weight: 600;
}

/* Bottom */
.side-bottom {
  padding: 12px 16px;
  border-top: 1px solid var(--line-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.role-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.logout-btn:hover {
  color: var(--danger);
  border-color: var(--danger);
}

/* === Right Area === */
.right-area {
  display: flex;
  flex-direction: column;
  height: 100vh;
  min-width: 0;
  overflow-y: scroll;
  scrollbar-width: none;          /* Firefox */
}
.right-area::-webkit-scrollbar {
  display: none;                  /* Chrome / Edge / Safari */
}

/* Top Bar */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 30;
  width: 100%;
  height: 52px;
  min-height: 52px;
  max-height: 52px;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 24px;
  box-sizing: border-box;
  flex-shrink: 0;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: 100px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.user-pill:hover {
  background: var(--bg-soft);
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.username {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
}

.chevron {
  color: var(--support);
  transition: transform var(--transition-fast);
}

.chevron.open {
  transform: rotate(90deg);
}

/* Dropdown */
.dropdown-overlay {
  position: fixed;
  top: 52px;
  right: 0;
  left: 220px;
  bottom: 0;
  z-index: 50;
}

.dropdown {
  position: absolute;
  top: 8px;
  right: 24px;
  width: 220px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 51;
}

.dropdown-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
}

.dropdown-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.dropdown-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.dropdown-info strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-info span {
  font-size: 11px;
  color: var(--support);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-divider {
  height: 1px;
  background: var(--line-soft);
  margin: 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  background: transparent;
  border: none;
  color: var(--ink);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--bg-soft);
}

.dropdown-item.danger {
  color: var(--danger);
}

.dropdown-item.danger:hover {
  background: var(--danger-soft);
}

/* Dropdown transition */
.dropdown-enter-active {
  transition: opacity 0.15s ease, transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* === Main === */
.side-main {
  flex: 1;
  padding: 0;
}

/* Page transition */
.page-enter-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-leave-active {
  transition: opacity 0.15s cubic-bezier(0.4, 0, 1, 1),
              transform 0.15s cubic-bezier(0.4, 0, 1, 1);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Footer */
.page-footer {
  border-top: 1px solid var(--line-soft);
  background: var(--bg);
  padding: 12px 32px;
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-link {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--support);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-link:hover {
  color: var(--muted);
}

.footer-copy {
  font-size: 11px;
  color: var(--support);
}

.footer-icp {
  font-size: 11px;
}

.icp-link {
  color: var(--support);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.icp-link:hover {
  color: var(--muted);
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar-layout {
    grid-template-columns: 1fr;
  }

  .side {
    position: static;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--line);
  }
}
</style>
