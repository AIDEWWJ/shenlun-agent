import type { RouteRecordRaw } from 'vue-router'

export const adminRoutes: RouteRecordRaw[] = [
  {
    path: '/admin',
    name: 'admin-home',
    component: () => import('../../../modules/admin/pages/AdminHomePage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../../../modules/admin/pages/AdminUsersPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/ai-configs',
    name: 'admin-ai-configs',
    component: () => import('../../../modules/admin/pages/AdminAiConfigsPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/email',
    name: 'admin-email',
    component: () => import('../../../modules/admin/pages/AdminEmailSettingsPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]
