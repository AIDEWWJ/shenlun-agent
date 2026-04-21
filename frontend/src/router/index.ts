import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { authStore, bootstrapAuth } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: () => (authStore.user ? '/workspace/profile' : '/auth'),
  },
  {
    path: '/auth',
    name: 'auth',
    component: () => import('../pages/AuthPage.vue'),
    meta: { public: true },
  },
  {
    path: '/workspace',
    component: () => import('../components/WorkspaceLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/workspace/profile',
      },
      {
        path: 'profile',
        name: 'workspace-profile',
        component: () => import('../pages/UserProfilePage.vue'),
        meta: { requiresAuth: true },
      },
      {
        path: 'admin-users',
        name: 'workspace-admin-users',
        component: () => import('../pages/AdminUsersPage.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'admin-ai-configs',
        name: 'workspace-admin-ai-configs',
        component: () => import('../pages/AdminAiConfigsPage.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'admin-emails',
        name: 'workspace-admin-emails',
        component: () => import('../pages/AdminEmailSettingsPage.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'debug',
        name: 'workspace-debug',
        component: () => import('../pages/ApiDebugPanel.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!authStore.initialized) {
    await bootstrapAuth()
  }

  if (to.meta.requiresAuth && !authStore.user) {
    return '/auth'
  }

  if (to.meta.requiresAdmin && !authStore.user?.roles.includes('admin')) {
    return '/workspace/profile'
  }

  if (to.path === '/auth' && authStore.user) {
    return '/workspace/profile'
  }

  return true
})

export default router
