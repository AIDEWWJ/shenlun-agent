import type { RouteRecordRaw } from 'vue-router'

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/auth',
    name: 'auth',
    component: () => import('../../../modules/auth/pages/AuthPage.vue'),
    meta: { immersive: true },
  },
]
