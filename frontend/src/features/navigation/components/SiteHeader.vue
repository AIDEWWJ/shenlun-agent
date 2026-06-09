<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { siteMeta } from '@/app/config/site'
import { logout } from '@/modules/auth/store'
import { useNavigationItems } from '../composables/useNavigationItems'

const route = useRoute()
const router = useRouter()
const { isAuthenticated, navItems } = useNavigationItems()
const menuOpen = ref(false)

function handleLogout() {
  logout()
  menuOpen.value = false
  void router.push('/')
}

function closeMenu() {
  menuOpen.value = false
}

// 路由变化时关闭菜单
watch(() => route.path, () => {
  menuOpen.value = false
})
</script>

<template>
  <!-- Mobile Overlay -->
  <teleport to="body">
    <transition name="overlay">
      <div v-if="menuOpen" class="mobile-backdrop" @click="closeMenu"></div>
    </transition>
  </teleport>

  <!-- Header Bar -->
  <header class="site-header">
    <div class="header-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-mark">申</span>
        <span class="brand-name">{{ siteMeta.shortName }}</span>
      </RouterLink>

      <nav class="nav-desktop" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="actions-desktop">
        <RouterLink v-if="isAuthenticated" to="/profile" class="action-link">个人中心</RouterLink>
        <RouterLink v-if="!isAuthenticated" to="/auth" class="action-btn-primary">登录</RouterLink>
        <button v-else type="button" class="action-link" @click="handleLogout">退出</button>
      </div>

      <button type="button" class="menu-btn" aria-label="菜单" @click="menuOpen = !menuOpen">
        <svg v-if="!menuOpen" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
        <svg v-else width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Dropdown Panel -->
    <transition name="dropdown">
      <div v-if="menuOpen" class="dropdown-panel">
        <nav class="dropdown-nav">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="dropdown-link"
            @click="closeMenu"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="dropdown-actions">
          <RouterLink v-if="isAuthenticated" to="/profile" class="dropdown-link" @click="closeMenu">个人中心</RouterLink>
          <RouterLink v-if="!isAuthenticated" to="/auth" class="dropdown-btn" @click="closeMenu">登录</RouterLink>
          <button v-else type="button" class="dropdown-link" @click="handleLogout">退出登录</button>
        </div>
      </div>
    </transition>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  box-shadow: var(--shadow-xs);
}

.header-inner {
  display: grid;
  grid-template-columns: 220px 1fr auto auto;
  align-items: center;
  height: 52px;
  gap: 24px;
  padding-right: 24px;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  padding: 0 16px;
  height: 100%;
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

/* Desktop Nav */
.nav-desktop {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-left: 8px;
}

.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  transition: all var(--transition-fast);
}

.nav-link:hover {
  color: var(--ink);
  background: var(--bg-soft);
}

.nav-link.router-link-active {
  color: var(--accent);
  background: var(--accent-soft);
  font-weight: 600;
}

/* Desktop Actions */
.actions-desktop {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.action-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  background: transparent;
  border: none;
  transition: all var(--transition-fast);
}

.action-link:hover {
  color: var(--ink);
  background: var(--bg-soft);
}

.action-btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  padding: 0 16px;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.action-btn-primary:hover {
  background: var(--accent-deep);
}

/* Mobile Menu Button */
.menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--ink);
}

/* Mobile Backdrop */
.mobile-backdrop {
  position: fixed;
  inset: 0;
  z-index: 39;
  background: rgba(0, 0, 0, 0.15);
}

/* Dropdown Panel - hangs below header */
.dropdown-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 41;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  padding: 8px 16px 12px;
}

.dropdown-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line-soft);
  margin-bottom: 8px;
}

.dropdown-link {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  transition: background var(--transition-fast);
}

.dropdown-link:hover,
.dropdown-link.router-link-active {
  background: var(--bg-soft);
  color: var(--accent);
}

.dropdown-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dropdown-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

/* Dropdown transition */
.dropdown-enter-active {
  transition: opacity 0.2s ease, transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.dropdown-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Backdrop transition */
.overlay-enter-active {
  transition: opacity 0.2s ease;
}
.overlay-leave-active {
  transition: opacity 0.15s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .nav-desktop,
  .actions-desktop {
    display: none;
  }

  .menu-btn {
    display: flex;
  }
}
</style>
