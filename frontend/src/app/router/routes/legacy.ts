import type { RouteRecordRaw } from 'vue-router'

export const legacyRoutes: RouteRecordRaw[] = [
  {
    path: '/workspace/home',
    redirect: '/',
  },
  {
    path: '/workspace/practice/:questionId',
    redirect: (to) => `/practice/${to.params.questionId}`,
  },
  {
    path: '/workspace/report/:reportId',
    redirect: (to) => `/reports/${to.params.reportId}`,
  },
  {
    path: '/workspace/history',
    redirect: '/history',
  },
  {
    path: '/workspace/profile',
    redirect: '/profile',
  },
  {
    path: '/workspace/ai-config',
    redirect: '/ai-config',
  },
  {
    path: '/workspace/admin-users',
    redirect: '/admin/users',
  },
  {
    path: '/workspace/admin-ai-configs',
    redirect: '/admin/ai-configs',
  },
  {
    path: '/workspace/admin-emails',
    redirect: '/admin/email',
  },
  {
    path: '/workspace/debug',
    redirect: '/about',
  },
  {
    path: '/workspace/about',
    redirect: '/about',
  },
  {
    path: '/workspace/:pathMatch(.*)*',
    redirect: '/',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]
