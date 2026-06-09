import type { RouteRecordRaw } from 'vue-router'

export const paperRoutes: RouteRecordRaw[] = [
  {
    path: '/papers',
    name: 'papers',
    component: () => import('../../../modules/paper/pages/PaperListPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/papers/:paperId',
    name: 'paper-detail',
    component: () => import('../../../modules/paper/pages/PaperDetailPage.vue'),
    meta: { requiresAuth: true },
  },
]
