import type { RouteRecordRaw } from 'vue-router'

export const homeRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../../../modules/home/pages/HomePage.vue'),
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../../../modules/home/pages/AboutPage.vue'),
  },
]
