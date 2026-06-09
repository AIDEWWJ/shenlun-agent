import type { NavigationGuardWithThis } from 'vue-router'

import { authStore, bootstrapAuth } from '@/modules/auth/store'

export const authGuard: NavigationGuardWithThis<undefined> = async (to) => {
  if (!authStore.initialized) {
    await bootstrapAuth()
  }

  if (to.meta.requiresAuth && !authStore.user) {
    return {
      path: '/auth',
      query: { redirect: to.fullPath },
    }
  }

  if (to.meta.requiresAdmin && !authStore.user?.roles.includes('admin')) {
    return '/'
  }

  if (to.path === '/auth' && authStore.user) {
    return String(to.query.redirect || '/papers')
  }

  return true
}
