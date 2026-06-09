import { computed } from 'vue'

import { authStore } from '@/modules/auth/store'

type NavIcon = 'home' | 'library' | 'history' | 'settings' | 'info' | 'admin'

type NavItem = {
  to: string
  label: string
  icon: NavIcon
}

export function useNavigationItems() {
  const isAdmin = computed(() => authStore.user?.roles.includes('admin') ?? false)
  const isAuthenticated = computed(() => Boolean(authStore.user))

  const navItems = computed<NavItem[]>(() => {
    const publicItems: NavItem[] = [
      { to: '/', label: '首页', icon: 'home' },
      { to: '/papers', label: '题库', icon: 'library' },
      { to: '/about', label: '关于', icon: 'info' },
    ]

    if (!isAuthenticated.value) {
      return publicItems
    }

    const privateItems: NavItem[] = [
      { to: '/', label: '首页', icon: 'home' },
      { to: '/papers', label: '题库', icon: 'library' },
      { to: '/history', label: '练习记录', icon: 'history' },
      { to: '/error-notebook', label: '错题本', icon: 'document' },
      { to: '/study-plan', label: '学习计划', icon: 'spark' },
    ]

    if (isAdmin.value) {
      privateItems.push({ to: '/admin', label: '管理后台', icon: 'admin' })
    }

    return privateItems
  })

  return {
    isAdmin,
    isAuthenticated,
    navItems,
  }
}
