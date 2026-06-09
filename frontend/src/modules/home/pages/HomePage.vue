<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { request } from '@/shared/api/http'
import { authStore } from '@/modules/auth/store'
import EmptyState from '@/shared/components/EmptyState.vue'
import AppIcon from '@/shared/components/AppIcon.vue'
import { getDashboard, getRecommendations } from '../services/dashboard.service'

const recentQuestions = ref<any[]>([])
const recentPractices = ref<any[]>([])
const recommendations = ref<any[]>([])
const dashboard = ref<any>(null)
const loading = ref(true)

const DASHBOARD_LIMIT = 5

const fetchDashboardData = async () => {
  try {
    const promises: Promise<any>[] = [
      request<any>(`/questions?page=1&page_size=${DASHBOARD_LIMIT}`, { token: authStore.token || undefined }).catch(() => null),
    ]

    if (authStore.token) {
      promises.push(
        request<any>(`/practice-records?page=1&page_size=${DASHBOARD_LIMIT}`, { token: authStore.token }).catch(() => null),
        getDashboard(authStore.token).catch(() => null),
        getRecommendations(authStore.token).catch(() => null),
      )
    }

    const results = await Promise.all(promises)
    if (results[0]?.items) recentQuestions.value = results[0].items
    if (results[1]?.items) recentPractices.value = results[1].items
    if (results[2]) dashboard.value = results[2]
    if (results[3]) recommendations.value = Array.isArray(results[3]) ? results[3] : results[3]?.items || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchDashboardData() })

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<template>
  <div class="home-page">
    <!-- Hero -->
    <section class="hero">
      <div class="shell hero-content">
        <div class="hero-text">
          <h1 class="hero-title">申论写作训练</h1>
          <p class="hero-subtitle">精选真题 · 沉浸书写 · AI 深度批改</p>
          <p class="hero-desc">
            系统化的申论练习平台，从选题到复盘形成完整闭环。每一次练习都有方向，每一份反馈都指向进步。
          </p>
          <div class="hero-actions">
            <RouterLink to="/papers" class="btn-primary">
              进入题库
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </RouterLink>
            <RouterLink v-if="!authStore.token" to="/auth" class="btn-ghost">
              登录账号
            </RouterLink>
          </div>
        </div>
        <div class="hero-features">
          <div class="feature-item">
            <span class="feature-num">01</span>
            <span class="feature-label">选题</span>
            <span class="feature-desc">按题型、年份精准筛选</span>
          </div>
          <div class="feature-item">
            <span class="feature-num">02</span>
            <span class="feature-label">作答</span>
            <span class="feature-desc">沉浸式双栏书写体验</span>
          </div>
          <div class="feature-item">
            <span class="feature-num">03</span>
            <span class="feature-label">批改</span>
            <span class="feature-desc">AI 多维度深度评估</span>
          </div>
          <div class="feature-item">
            <span class="feature-num">04</span>
            <span class="feature-label">复盘</span>
            <span class="feature-desc">对照参考持续改进</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Bar (logged in) -->
    <section v-if="authStore.token && dashboard" class="stats-bar shell">
      <div class="stat-card">
        <span class="stat-num">{{ dashboard.total_practices ?? dashboard.practice_count ?? 0 }}</span>
        <span class="stat-label">练习次数</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ dashboard.avg_score ?? dashboard.average_score ?? '-' }}</span>
        <span class="stat-label">平均分</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ dashboard.total_reviews ?? dashboard.review_count ?? 0 }}</span>
        <span class="stat-label">批改报告</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ dashboard.streak ?? dashboard.days_active ?? 0 }}</span>
        <span class="stat-label">连续天数</span>
      </div>
    </section>

    <!-- Quick Actions (logged in) -->
    <section v-if="authStore.token" class="quick-actions shell">
      <RouterLink to="/error-notebook" class="quick-card">
        <AppIcon name="document" :size="18" />
        <span>错题本</span>
      </RouterLink>
      <RouterLink to="/study-plan" class="quick-card">
        <AppIcon name="spark" :size="18" />
        <span>学习计划</span>
      </RouterLink>
      <RouterLink to="/history" class="quick-card">
        <AppIcon name="history" :size="18" />
        <span>练习记录</span>
      </RouterLink>
    </section>

    <!-- Dashboard -->
    <main class="dashboard shell">
      <!-- Recommendations -->
      <section v-if="recommendations.length > 0" class="section-card recommend-card">
        <div class="section-head">
          <h2 class="section-title">推荐练习</h2>
        </div>
        <div class="recommend-list">
          <RouterLink
            v-for="item in recommendations.slice(0, 3)"
            :key="item.id"
            :to="`/practice/${item.id}`"
            class="recommend-item"
          >
            <span class="recommend-type">{{ item.question_type || '综合题' }}</span>
            <h3>{{ item.title }}</h3>
            <span class="recommend-reason">{{ item.reason || item.source || '' }}</span>
          </RouterLink>
        </div>
      </section>

      <div class="dashboard-grid">
        <!-- Questions -->
        <section class="section-card">
          <div class="section-head">
            <h2 class="section-title">精选题库</h2>
            <RouterLink to="/papers" class="section-link">
              全部题目
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </RouterLink>
          </div>

          <div v-if="loading" class="skeleton-list">
            <div v-for="i in 3" :key="i" class="skeleton-row"></div>
          </div>
          <div v-else-if="recentQuestions.length === 0">
            <EmptyState
              title="题库整备中"
              description="题库正在更新，请稍后查看。"
              actionLabel="了解更多"
              actionTo="/about"
            />
          </div>
          <div v-else class="item-list">
            <RouterLink
              v-for="item in recentQuestions"
              :key="item.id"
              :to="`/practice/${item.id}`"
              class="question-row"
            >
              <div class="question-row-main">
                <span class="question-type">{{ item.question_type }}</span>
                <h3 class="question-row-title">{{ item.title }}</h3>
                <span class="question-source">{{ item.source }}</span>
              </div>
              <span class="row-arrow">→</span>
            </RouterLink>
          </div>
        </section>

        <!-- Practice Records -->
        <section class="section-card">
          <div class="section-head">
            <h2 class="section-title">练习记录</h2>
            <RouterLink v-if="authStore.token" to="/history" class="section-link">
              全部记录
              <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
            </RouterLink>
          </div>

          <div v-if="loading" class="skeleton-list">
            <div v-for="i in 3" :key="i" class="skeleton-row"></div>
          </div>
          <div v-else-if="!authStore.token" class="empty-hint">
            <p>登录后查看练习记录与 AI 批改报告。</p>
            <RouterLink to="/auth" class="btn-small">立即登录</RouterLink>
          </div>
          <div v-else-if="recentPractices.length === 0" class="empty-hint">
            <p>还没有练习记录，从题库开始第一次练习吧。</p>
            <RouterLink to="/papers" class="btn-small">前往题库</RouterLink>
          </div>
          <div v-else class="item-list">
            <RouterLink
              v-for="record in recentPractices"
              :key="record.id"
              :to="`/reports/${record.review_id}`"
              class="practice-row"
            >
              <div class="practice-row-main">
                <span class="practice-date">{{ formatDate(record.created_at) }}</span>
                <h3 class="practice-row-title">{{ record.question_title || '未命名题目' }}</h3>
              </div>
              <span v-if="record.score" class="practice-score">{{ record.score }}</span>
              <span v-else class="row-arrow">→</span>
            </RouterLink>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
}

/* Hero */
.hero {
  padding: 64px 0 48px;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  box-shadow: var(--shadow-xs);
}

.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 56px;
  align-items: center;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-title {
  font-size: 40px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 15px;
  color: var(--accent);
  font-weight: 600;
  letter-spacing: 0.02em;
}

.hero-desc {
  font-size: 14px;
  color: var(--muted);
  max-width: 420px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.btn-primary:hover {
  background: var(--accent-deep);
  box-shadow: var(--shadow-md);
}

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 22px;
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.btn-ghost:hover {
  border-color: var(--line-strong);
  background: var(--bg-soft);
}

/* Features */
.hero-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 22px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-fast);
}

.feature-item:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.feature-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.04em;
}

.feature-label {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-serif);
}

.feature-desc {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

/* Dashboard */
.dashboard {
  padding: 32px 0 80px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 28px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 18px 12px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-serif);
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: var(--muted);
}

/* Quick Actions */
.quick-actions {
  display: flex;
  gap: 10px;
  padding-top: 8px;
}

.quick-card {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  transition: all var(--transition-fast);
}

.quick-card:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* Recommendations */
.recommend-card {
  margin-bottom: 4px;
}

.recommend-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.recommend-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  background: var(--bg-soft);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.recommend-item:hover {
  border-color: var(--accent);
  background: var(--paper);
}

.recommend-type {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
}

.recommend-item h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  font-family: var(--font-sans);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recommend-reason {
  font-size: 11px;
  color: var(--support);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

/* Section Card */
.section-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-soft);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-sans);
}

.section-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  transition: opacity var(--transition-fast);
}

.section-link:hover {
  opacity: 0.8;
}

/* Item Lists */
.item-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-row,
.practice-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-soft);
  transition: all var(--transition-fast);
}

.question-row:hover,
.practice-row:hover {
  background: var(--paper);
  border-color: var(--line-strong);
  box-shadow: var(--shadow-xs);
}

.question-row-main,
.practice-row-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.question-type {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
}

.question-row-title,
.practice-row-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  font-family: var(--font-sans);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-source {
  font-size: 11px;
  color: var(--support);
}

.practice-date {
  font-size: 11px;
  color: var(--support);
  font-weight: 500;
}

.practice-score {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-serif);
  flex-shrink: 0;
}

.row-arrow {
  color: var(--support);
  font-size: 14px;
  flex-shrink: 0;
  transition: color var(--transition-fast);
}

.question-row:hover .row-arrow,
.practice-row:hover .row-arrow {
  color: var(--accent);
}

/* Empty Hint */
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
  text-align: center;
}

.empty-hint p {
  font-size: 13px;
  color: var(--muted);
}

.btn-small {
  display: inline-flex;
  align-items: center;
  padding: 7px 16px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.btn-small:hover {
  background: var(--accent-hover);
}

/* Skeleton */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-row {
  height: 56px;
  background: var(--bg-soft);
  border-radius: var(--radius-lg);
  animation: pulse 2s ease infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Responsive */
@media (max-width: 900px) {
  .hero-content {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .hero {
    padding: 48px 0 40px;
  }

  .hero-title {
    font-size: 32px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .hero {
    padding: 32px 0 28px;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-subtitle {
    font-size: 13px;
  }

  .hero-desc {
    font-size: 13px;
  }

  .hero-features {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .feature-item {
    padding: 14px;
  }

  .feature-label {
    font-size: 14px;
  }

  .feature-desc {
    font-size: 11px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-ghost {
    justify-content: center;
  }

  .dashboard {
    padding: 24px 0 48px;
  }

  .dashboard-grid {
    gap: 16px;
  }

  .section-card {
    padding: 16px;
    border-radius: var(--radius-lg);
  }

  .section-head {
    margin-bottom: 14px;
    padding-bottom: 10px;
  }

  .section-title {
    font-size: 15px;
  }

  .question-row,
  .practice-row {
    padding: 12px;
  }

  .question-row-title,
  .practice-row-title {
    font-size: 13px;
  }

  .practice-score {
    font-size: 18px;
  }
}
</style>
