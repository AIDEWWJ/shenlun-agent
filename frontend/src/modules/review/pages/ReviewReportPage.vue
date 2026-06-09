<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { request } from '@/shared/api/http'
import { authStore } from '@/modules/auth/store'

import DimensionScoreList from '@/features/review-report/components/DimensionScoreList.vue'
import RewritePanel from '@/features/review-report/components/RewritePanel.vue'
import ScoreSummary from '@/features/review-report/components/ScoreSummary.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import AppIcon from '@/shared/components/AppIcon.vue'
import { useReviewTabs } from '../composables/useReviewTabs'
import { askReviewQuestion, listReviewQA } from '../services/review-api.service'

const route = useRoute()
const reviewId = Number(route.params.reportId)
const { activeTab, setActiveTab } = useReviewTabs()

const report = ref<any>(null)
const loading = ref(true)

// Q&A state
const qaMessages = ref<any[]>([])
const qaInput = ref('')
const qaLoading = ref(false)
const qaConversationId = ref<string | undefined>(undefined)

const fetchReport = async () => {
  try {
    const res = await request<any>(`/reviews/${reviewId}`, { token: authStore.token || undefined })
    report.value = res
  } catch (err) {
    console.error('Failed to fetch review report:', err)
  } finally {
    loading.value = false
  }
}

const fetchQA = async () => {
  if (!authStore.token) return
  try {
    const res = await listReviewQA(authStore.token, reviewId, { conversation_id: qaConversationId.value })
    qaMessages.value = res?.items || res || []
  } catch {}
}

const handleAskQuestion = async () => {
  if (!authStore.token || !qaInput.value.trim()) return
  qaLoading.value = true
  try {
    const res = await askReviewQuestion(authStore.token, reviewId, {
      question: qaInput.value.trim(),
      conversation_id: qaConversationId.value,
    })
    if (res?.conversation_id) qaConversationId.value = res.conversation_id
    // Add to messages
    qaMessages.value.push({ role: 'user', content: qaInput.value.trim() })
    if (res?.answer || res?.content) {
      qaMessages.value.push({ role: 'assistant', content: res.answer || res.content })
    }
    qaInput.value = ''
  } catch (err) {
    console.error('QA failed:', err)
  } finally {
    qaLoading.value = false
  }
}

onMounted(() => { fetchReport(); fetchQA() })

const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const strengthsArray = computed(() => report.value?.strengths ? report.value.strengths.split('\n').filter(Boolean) : [])
const issuesArray = computed(() => report.value?.issues ? report.value.issues.split('\n').filter(Boolean) : [])

const mappedDimensions = computed(() => {
  if (!report.value || !report.value.score_breakdown) return []
  const breakdown = report.value.score_breakdown
  return Object.keys(breakdown).map(key => {
    const item = breakdown[key]
    return { name: key, score: item.score || 0, maxScore: item.max_score || 100, comment: item.comment || '' }
  })
})
</script>

<template>
  <div class="report-page">
    <div class="report-container">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="skeleton-block" style="height: 180px"></div>
        <div class="skeleton-block" style="height: 400px"></div>
      </div>

      <!-- Not Found -->
      <EmptyState
        v-else-if="!report"
        title="报告不存在"
        description="该报告可能已被删除或无权查看。"
        action-label="返回练习记录"
        action-to="/history"
      />

      <template v-else>
        <!-- Header -->
        <header class="report-header">
          <div class="report-header-main">
            <div class="report-meta">
              <span class="report-badge">AI 批改报告</span>
              <span class="report-date">{{ formatDate(report.created_at) }}</span>
            </div>
            <h1 class="report-title">{{ report.question_title || '未命名题目' }}</h1>
            <div class="report-info">
              <span v-if="report.question_type">{{ report.question_type }}</span>
              <span v-if="report.model_name || report.model_provider">{{ report.model_name || report.model_provider }}</span>
            </div>
          </div>
          <div class="report-score-block">
            <span class="score-label">综合得分</span>
            <strong class="score-value">{{ report.score ?? '-' }}</strong>
          </div>
        </header>

        <!-- Summary -->
        <section class="report-summary">
          <h3 class="summary-label">总评</h3>
          <p class="summary-text">{{ report.summary || '暂无总结内容' }}</p>
        </section>

        <!-- Tabs -->
        <section class="report-detail">
          <div class="detail-tabs">
            <button
              class="detail-tab"
              :class="{ active: activeTab === 'summary' }"
              @click="setActiveTab('summary')"
            >分项解析</button>
            <button
              class="detail-tab"
              :class="{ active: activeTab === 'rewrite' }"
              @click="setActiveTab('rewrite')"
            >原文对照</button>
            <button
              class="detail-tab"
              :class="{ active: activeTab === 'qa' }"
              @click="setActiveTab('qa')"
            >答疑追问</button>
          </div>

          <!-- Summary Tab -->
          <div v-if="activeTab === 'summary'" class="detail-content">
            <!-- Strengths & Issues -->
            <div class="two-col">
              <div class="feedback-card">
                <h4 class="feedback-title feedback-title-good">亮点与优势</h4>
                <ul class="feedback-list">
                  <li v-for="(item, i) in strengthsArray" :key="i">{{ item }}</li>
                  <li v-if="strengthsArray.length === 0" class="feedback-empty">暂无</li>
                </ul>
              </div>
              <div class="feedback-card">
                <h4 class="feedback-title feedback-title-issue">问题与不足</h4>
                <ul class="feedback-list">
                  <li v-for="(item, i) in issuesArray" :key="i">{{ item }}</li>
                  <li v-if="issuesArray.length === 0" class="feedback-empty">暂无</li>
                </ul>
              </div>
            </div>

            <!-- Suggestions -->
            <div v-if="report.suggestions" class="suggestions-card">
              <h4 class="suggestions-title">改进建议</h4>
              <p class="suggestions-text">{{ report.suggestions }}</p>
            </div>

            <!-- Dimensions -->
            <div class="dimensions-section">
              <h4 class="dimensions-title">维度得分</h4>
              <DimensionScoreList :dimensions="mappedDimensions" />
            </div>
          </div>

          <!-- Rewrite Tab -->
          <RewritePanel
            v-else-if="activeTab === 'rewrite'"
            :answer-text="report.answer_content"
            :reference-answer="report.report?.reference_answer || '暂无参考答案'"
            :optimized-example="report.report?.optimized_example || '暂无优化示例'"
          />

          <!-- Q&A Tab -->
          <div v-else-if="activeTab === 'qa'" class="detail-content qa-section">
            <div class="qa-messages" v-if="qaMessages.length > 0">
              <div
                v-for="(msg, i) in qaMessages"
                :key="i"
                class="qa-msg"
                :class="msg.role === 'user' ? 'qa-msg-user' : 'qa-msg-ai'"
              >
                <div class="qa-msg-label">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
                <div class="qa-msg-content">{{ msg.content || msg.answer || msg.question }}</div>
              </div>
            </div>
            <div v-else class="qa-empty">
              <AppIcon name="spark" :size="20" />
              <p>针对这份批改报告提出你的疑问，AI 会为你解答。</p>
            </div>

            <div class="qa-input-area">
              <input
                v-model="qaInput"
                type="text"
                class="qa-input"
                placeholder="输入你的问题..."
                @keydown.enter="handleAskQuestion"
                :disabled="qaLoading"
              />
              <button
                type="button"
                class="qa-send-btn"
                :disabled="qaLoading || !qaInput.trim()"
                @click="handleAskQuestion"
              >
                {{ qaLoading ? '思考中...' : '发送' }}
              </button>
            </div>
          </div>
        </section>

        <!-- Actions -->
        <footer class="report-footer">
          <RouterLink to="/history" class="footer-btn footer-btn-ghost">返回记录</RouterLink>
          <RouterLink :to="`/practice/${report.question_id}`" class="footer-btn footer-btn-primary">重新练习</RouterLink>
        </footer>
      </template>
    </div>
  </div>
</template>

<style scoped>
.report-page {
  min-height: 100vh;
  background: var(--bg);
  padding: 40px 24px 80px;
}

.report-container {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-block {
  background: var(--bg-soft);
  border-radius: var(--radius-xl);
  border: 1px solid var(--line-soft);
  animation: pulse 2s ease infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Header */
.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.report-badge {
  padding: 3px 10px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  border-radius: 100px;
}

.report-date {
  font-size: 12px;
  color: var(--support);
}

.report-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 8px;
}

.report-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--muted);
}

.report-score-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 24px;
  background: var(--bg-soft);
  border-radius: var(--radius-lg);
  border: 1px solid var(--line);
  flex-shrink: 0;
}

.score-label {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
}

.score-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-serif);
  line-height: 1;
}

/* Summary */
.report-summary {
  padding: 24px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.summary-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 10px;
  font-family: var(--font-sans);
}

.summary-text {
  font-size: 14px;
  line-height: 1.9;
  color: var(--muted);
}

/* Detail */
.report-detail {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--line);
}

.detail-tab {
  padding: 14px 24px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
}

.detail-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.detail-tab:not(.active):hover {
  color: var(--ink);
}

.detail-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Two Col */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feedback-card {
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.feedback-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-sans);
}

.feedback-title-good { color: var(--success); }
.feedback-title-good::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
}

.feedback-title-issue { color: var(--danger); }
.feedback-title-issue::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--danger);
}

.feedback-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback-list li {
  font-size: 13px;
  line-height: 1.7;
  color: var(--muted);
  padding-left: 14px;
  position: relative;
}

.feedback-list li::before {
  content: '–';
  position: absolute;
  left: 0;
  color: var(--support);
}

.feedback-empty {
  color: var(--support);
  font-style: italic;
}

/* Suggestions */
.suggestions-card {
  padding: 20px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.suggestions-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 10px;
  font-family: var(--font-sans);
}

.suggestions-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--muted);
  white-space: pre-wrap;
}

/* Dimensions */
.dimensions-section {
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.dimensions-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 16px;
  font-family: var(--font-sans);
}

/* Footer */
.report-footer {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.footer-btn {
  padding: 10px 24px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.footer-btn-ghost {
  background: var(--paper);
  border: 1px solid var(--line);
  color: var(--ink);
}

.footer-btn-ghost:hover {
  border-color: var(--line-strong);
  background: var(--bg-soft);
}

.footer-btn-primary {
  background: var(--accent);
  color: #fff;
}

.footer-btn-primary:hover {
  background: var(--accent-deep);
}

/* Q&A Section */
.qa-section {
  min-height: 300px;
}

.qa-messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding-bottom: 16px;
}

.qa-msg {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  max-width: 85%;
}

.qa-msg-user {
  align-self: flex-end;
  background: var(--accent-soft);
}

.qa-msg-ai {
  align-self: flex-start;
  background: var(--bg-soft);
  border: 1px solid var(--line-soft);
}

.qa-msg-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--support);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.qa-msg-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink);
  white-space: pre-wrap;
}

.qa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 24px;
  color: var(--support);
  text-align: center;
}

.qa-empty p {
  font-size: 13px;
  color: var(--muted);
  max-width: 320px;
}

.qa-input-area {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--line-soft);
}

.qa-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--paper);
  font-size: 13px;
  color: var(--ink);
  outline: none;
  transition: border-color var(--transition-fast);
}

.qa-input:focus {
  border-color: var(--accent);
}

.qa-input::placeholder {
  color: var(--support);
}

.qa-send-btn {
  padding: 10px 18px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.qa-send-btn:hover:not(:disabled) {
  background: var(--accent-deep);
}

.qa-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 640px) {
  .report-page {
    padding: 20px 16px 60px;
  }

  .report-header {
    flex-direction: column;
    padding: 20px;
  }

  .two-col {
    grid-template-columns: 1fr;
  }

  .report-title {
    font-size: 18px;
  }
}
</style>
