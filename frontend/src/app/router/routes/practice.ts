import type { RouteRecordRaw } from 'vue-router'

export const practiceRoutes: RouteRecordRaw[] = [
  {
    path: '/practice/paper/:paperId',
    name: 'paper-practice',
    component: () => import('../../../modules/practice/pages/PaperPracticePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/practice/:questionId',
    name: 'practice-session',
    component: () => import('../../../modules/practice/pages/PracticeSessionPage.vue'),
    meta: { immersive: true, requiresAuth: true },
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../../../modules/practice/pages/HistoryPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/error-notebook',
    name: 'error-notebook',
    component: () => import('../../../modules/practice/pages/ErrorNotebookPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/study-plan',
    name: 'study-plan',
    component: () => import('../../../modules/practice/pages/StudyPlanPage.vue'),
    meta: { requiresAuth: true },
  },
]
