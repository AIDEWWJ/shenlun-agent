import type { RouteRecordRaw } from 'vue-router'

export const reviewRoutes: RouteRecordRaw[] = [
  {
    path: '/reports/:reportId',
    name: 'review-report',
    component: () => import('../../../modules/review/pages/ReviewReportPage.vue'),
    meta: { immersive: true, requiresAuth: true },
  },
]
