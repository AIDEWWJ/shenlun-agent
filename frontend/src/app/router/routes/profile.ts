import type { RouteRecordRaw } from 'vue-router'

export const profileRoutes: RouteRecordRaw[] = [
  {
    path: '/profile',
    redirect: '/profile/basic',
  },
  {
    path: '/profile/basic',
    name: 'profile-basic',
    component: () => import('../../../modules/profile/pages/ProfileBasicPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/security',
    name: 'profile-security',
    component: () => import('../../../modules/profile/pages/ProfileSecurityPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/ai-config',
    redirect: '/profile/ai-config',
  },
  {
    path: '/profile/ai-config',
    name: 'profile-ai-config',
    component: () => import('../../../modules/profile/pages/ProfileAiConfigPage.vue'),
    meta: { requiresAuth: true },
  },
]
