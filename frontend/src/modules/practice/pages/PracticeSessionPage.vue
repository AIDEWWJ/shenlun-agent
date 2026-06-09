<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { getWorkspace } from '@/modules/question/services/workspace.service'
import { getCurrentSession, createSession, submitSession } from '../services/practice.service'
import { createAnswer, updateAnswer } from '../services/answer.service'

const route = useRoute()
const router = useRouter()
const questionId = Number(route.params.questionId)

const workspace = ref<any>(null)
const session = ref<any>(null)
const currentAnswer = ref<any>(null)
const answerContent = ref('')
const activeMaterialIndex = ref(0)
const loading = ref(true)
const submitting = ref(false)
const saving = ref(false)
const error = ref('')
const materialsExpanded = ref(false)

const materials = ref<any[]>([])
const question = computed(() => workspace.value?.question || {})
const wordCount = computed(() => answerContent.value.replace(/\s/g, '').length)

async function loadWorkspace() {
  if (!authStore.token) { router.push('/auth'); return }
  loading.value = true
  try {
    const res = await getWorkspace(authStore.token, questionId)
    workspace.value = res
    materials.value = res?.materials || res?.question?.materials || []

    try {
      const sess = await getCurrentSession(authStore.token, questionId)
      session.value = sess
    } catch {
      const newSess = await createSession(authStore.token, { question_id: questionId })
      session.value = newSess
    }

    if (res?.latest_answer?.content) {
      answerContent.value = res.latest_answer.content
      currentAnswer.value = res.latest_answer
    } else if (res?.draft_content) {
      answerContent.value = res.draft_content
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function saveAnswer() {
  if (!authStore.token || !answerContent.value.trim()) return
  saving.value = true
  try {
    if (currentAnswer.value?.id) {
      await updateAnswer(authStore.token, currentAnswer.value.id, { content: answerContent.value })
    } else {
      const res = await createAnswer(authStore.token, { question_id: questionId, content: answerContent.value })
      currentAnswer.value = res
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  if (!authStore.token || !session.value?.id) return
  submitting.value = true
  error.value = ''
  try {
    await saveAnswer()
    const result = await submitSession(authStore.token, session.value.id)
    const reviewId = result?.review_id || result?.id
    if (reviewId) {
      router.push(`/reports/${reviewId}`)
    } else {
      router.push('/history')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '提交失败'
  } finally {
    submitting.value = false
  }
}

onMounted(() => { void loadWorkspace() })
</script>

<template>
  <div class="practice-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- Error -->
    <div v-else-if="error && !workspace" class="error-state">
      <p>{{ error }}</p>
      <button type="button" @click="router.push('/papers')">返回题库</button>
    </div>

    <!-- Main -->
    <template v-else-if="workspace">
      <!-- Top Bar -->
      <header class="topbar">
        <button type="button" class="back-btn" @click="router.push('/papers')">
          <AppIcon name="chevron-right" :size="14" style="transform: rotate(180deg)" />
          返回题库
        </button>
        <div class="topbar-info">
          <span v-if="question.question_type" class="topbar-tag">{{ question.question_type }}</span>
          <span v-if="question.region" class="topbar-tag">{{ question.region }}</span>
          <span v-if="question.year" class="topbar-tag">{{ question.year }}</span>
          <span v-if="question.difficulty" class="topbar-tag" :class="question.difficulty">{{ question.difficulty }}</span>
        </div>
        <div class="topbar-right">
          <span class="word-count">{{ wordCount }} 字</span>
          <span v-if="saving" class="save-indicator">保存中...</span>
        </div>
      </header>

      <!-- Content -->
      <div class="content-area">
        <!-- Requirement Section -->
        <section class="section requirement-section">
          <div class="section-header">
            <AppIcon name="edit" :size="16" />
            <h2>作答要求</h2>
          </div>
          <div class="requirement-body">
            <pre class="requirement-text">{{ question.requirement || question.content || '暂无要求' }}</pre>
          </div>
        </section>

        <!-- Materials Section -->
        <section v-if="materials.length > 0" class="section materials-section">
          <div class="section-header" @click="materialsExpanded = !materialsExpanded">
            <div class="section-header-left">
              <AppIcon name="document" :size="16" />
              <h2>给定资料</h2>
              <span class="material-count">{{ materials.length }} 篇</span>
            </div>
            <div class="section-header-right">
              <span v-if="!materialsExpanded" class="expand-hint">点击展开</span>
              <AppIcon :name="materialsExpanded ? 'chevron-right' : 'chevron-right'" :size="14" class="expand-icon" :class="{ expanded: materialsExpanded }" />
            </div>
          </div>

          <!-- Material Tabs (always visible) -->
          <div v-if="materials.length > 1" class="material-tabs">
            <button
              v-for="(m, i) in materials"
              :key="i"
              type="button"
              @click="activeMaterialIndex = i; materialsExpanded = true"
              class="material-tab"
              :class="{ active: activeMaterialIndex === i }"
            >
              材料 {{ m.material_num || i + 1 }}
            </button>
          </div>

          <!-- Material Content -->
          <div v-if="materialsExpanded" class="material-content">
            <pre class="material-text">{{ materials[activeMaterialIndex]?.content || '' }}</pre>
          </div>
          <div v-else class="material-preview" @click="materialsExpanded = true">
            <pre class="material-text">{{ (materials[activeMaterialIndex]?.content || '').substring(0, 150) }}...</pre>
          </div>
        </section>

        <!-- Answer Section -->
        <section class="section answer-section">
          <div class="section-header">
            <AppIcon name="edit" :size="16" />
            <h2>你的答案</h2>
          </div>
          <div class="answer-body">
            <textarea
              v-model="answerContent"
              class="answer-input"
              placeholder="在此输入你的答案..."
              @blur="saveAnswer"
            ></textarea>
          </div>
        </section>
      </div>

      <!-- Bottom Bar -->
      <footer class="bottombar">
        <div class="bottombar-left">
          <span v-if="error" class="error-msg">{{ error }}</span>
        </div>
        <div class="bottombar-right">
          <button type="button" class="btn btn-secondary" @click="saveAnswer" :disabled="saving || !answerContent.trim()">
            保存草稿
          </button>
          <button type="button" class="btn btn-primary" @click="handleSubmit" :disabled="submitting || !answerContent.trim()">
            {{ submitting ? '提交中...' : '提交批改' }}
          </button>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.practice-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
}

.loading-state, .error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--muted);
}

.error-state button {
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
}

/* Top Bar */
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
  transition: color var(--transition-fast);
}
.back-btn:hover { color: var(--accent); }

.topbar-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.topbar-tag {
  padding: 2px 8px;
  background: var(--bg-soft);
  color: var(--muted);
  font-size: 11px;
  font-weight: 500;
  border-radius: 100px;
}
.topbar-tag.简单 { background: #dcfce7; color: #166534; }
.topbar-tag.中等 { background: #fef9c3; color: #854d0e; }
.topbar-tag.困难 { background: #fee2e2; color: #991b1b; }

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.word-count {
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
}

.save-indicator {
  font-size: 12px;
  color: var(--accent);
}

/* Content Area */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Sections */
.section {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line-soft);
  color: var(--ink);
}

.section-header h2 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.section-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.material-count {
  font-size: 11px;
  color: var(--support);
  padding: 1px 6px;
  background: var(--bg-soft);
  border-radius: 100px;
}

.expand-hint {
  font-size: 11px;
  color: var(--support);
}

.expand-icon {
  color: var(--support);
  transition: transform var(--transition-fast);
}
.expand-icon.expanded {
  transform: rotate(90deg);
}

/* Requirement */
.requirement-body {
  padding: 16px;
}

.requirement-text {
  font-size: 14px;
  color: var(--ink);
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

/* Materials */
.materials-section .section-header {
  cursor: pointer;
  transition: background var(--transition-fast);
}
.materials-section .section-header:hover {
  background: var(--bg-soft);
}

.material-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--line-soft);
  overflow-x: auto;
}

.material-tab {
  padding: 4px 12px;
  border: 1px solid var(--line);
  border-radius: 100px;
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.material-tab:hover {
  border-color: var(--line-strong);
  color: var(--ink);
}
.material-tab.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.material-content, .material-preview {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.material-preview {
  cursor: pointer;
  opacity: 0.8;
  transition: opacity var(--transition-fast);
}
.material-preview:hover {
  opacity: 1;
}

.material-text {
  font-size: 13px;
  color: var(--ink);
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

/* Answer */
.answer-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.answer-body {
  flex: 1;
  padding: 0;
}

.answer-input {
  width: 100%;
  height: 100%;
  min-height: 250px;
  padding: 16px;
  border: none;
  background: transparent;
  font-size: 14px;
  color: var(--ink);
  line-height: 1.8;
  resize: none;
  outline: none;
  font-family: inherit;
}

.answer-input::placeholder {
  color: var(--support);
}

/* Bottom Bar */
.bottombar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--paper);
  border-top: 1px solid var(--line);
  flex-shrink: 0;
}

.bottombar-left {
  flex: 1;
}

.error-msg {
  font-size: 12px;
  color: var(--danger);
}

.bottombar-right {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 20px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.btn-secondary {
  background: var(--paper);
  border: 1px solid var(--line);
  color: var(--ink);
}
.btn-secondary:hover:not(:disabled) {
  border-color: var(--line-strong);
}
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-deep);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .topbar {
    flex-wrap: wrap;
    gap: 8px;
  }
  .topbar-info {
    order: 3;
    width: 100%;
  }
  .content-area {
    padding: 12px;
  }
}
</style>
