import { createRouter, createWebHistory } from 'vue-router'

import { authGuard } from './guards'
import { adminRoutes } from './routes/admin'
import { authRoutes } from './routes/auth'
import { homeRoutes } from './routes/home'
import { legacyRoutes } from './routes/legacy'
import { paperRoutes } from './routes/paper'
import { practiceRoutes } from './routes/practice'
import { profileRoutes } from './routes/profile'
import { questionRoutes } from './routes/question'
import { reviewRoutes } from './routes/review'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...homeRoutes,
    ...paperRoutes,
    ...questionRoutes,
    ...practiceRoutes,
    ...reviewRoutes,
    ...profileRoutes,
    ...authRoutes,
    ...adminRoutes,
    ...legacyRoutes,
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(authGuard)

export default router
