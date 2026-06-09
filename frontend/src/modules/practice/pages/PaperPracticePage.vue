<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { getPaperDetail } from '@/modules/paper/services/paper.service'
import { getPaperSession, savePaperSession, deletePaperSession } from '../services/paper-session.service'
import type { PaperDetail } from '@/modules/paper/types/paper'

const route = useRoute()
const router = useRouter()
const paperId = Number(route.params.paperId)

const paper = ref<PaperDetail | null>(null)
const loading = ref(true)
const currentIndex = ref(0)
const answers = ref<Record<number, string>>({})
const showMaterials = ref(false)
const timerSeconds = ref(0)
const saveStatus = ref<'saved' | 'saving' | 'unsaved'>('saved')
const showResumeDialog = ref(false)
const serverSession = ref<any>(null)
let timerInterval: ReturnType<typeof setInterval> | null = null
let autoSaveInterval: ReturnType<typeof setInterval> | null = null
const STORAGE_KEY = `paper-practice-${paperId}`

const currentQuestion = computed(() => paper.value?.questions[currentIndex.value])
const currentAnswer = computed(() => answers.value[currentQuestion.value?.id || 0] || '')
const wordCount = computed(() => currentAnswer.value.replace(/\s/g, '').length)
const totalQuestions = computed(() => paper.value?.questions.length || 0)
const answeredCount = computed(() => Object.values(answers.value).filter(a => a?.trim()).length)

const currentMaterials = computed(() => {
  if (!currentQuestion.value?.material_refs || !paper.value) return []
  const refs = currentQuestion.value.material_refs.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
  return paper.value.materials.filter(m => refs.includes(m.material_num))
})

// Timer
function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function startTimer() {
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => { timerSeconds.value++ }, 1000)
}

async function loadPaper() {
  loading.value = true
  try {
    paper.value = await getPaperDetail(authStore.token || '', paperId)
  } catch (e) {
    console.error('Failed to load paper:', e)
  } finally {
    loading.value = false
  }
}

async function checkServerSession() {
  if (!authStore.token) return false
  try {
    const session = await getPaperSession(authStore.token, paperId)
    if (session && session.answers && Object.values(session.answers).some(a => a?.trim())) {
      serverSession.value = session
      return true
    }
  } catch {}
  return false
}

function loadFromServerSession() {
  if (!serverSession.value) return
  answers.value = serverSession.value.answers || {}
  currentIndex.value = serverSession.value.current_index || 0
  timerSeconds.value = serverSession.value.timer_seconds || 0
}

function loadFromLocalStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return false
    const data = JSON.parse(raw)
    if (data.answers) answers.value = data.answers
    if (typeof data.currentIndex === 'number') currentIndex.value = data.currentIndex
    if (typeof data.timerSeconds === 'number') timerSeconds.value = data.timerSeconds
    return true
  } catch {
    return false
  }
}

function saveToLocalStorage() {
  try {
    const data = {
      answers: answers.value,
      currentIndex: currentIndex.value,
      timerSeconds: timerSeconds.value,
      savedAt: Date.now(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.error('Failed to save to localStorage:', e)
  }
}

async function saveToServer() {
  if (!authStore.token) return
  saveStatus.value = 'saving'
  try {
    await savePaperSession(authStore.token, paperId, {
      answers: answers.value,
      current_index: currentIndex.value,
      timer_seconds: timerSeconds.value,
    })
    saveStatus.value = 'saved'
  } catch (e) {
    console.error('Failed to save to server:', e)
    saveStatus.value = 'unsaved'
  }
}

function clearAll() {
  localStorage.removeItem(STORAGE_KEY)
}

function goToQuestion(index: number) {
  if (index >= 0 && index < totalQuestions.value) {
    currentIndex.value = index
    showMaterials.value = false
  }
}

function updateAnswer(value: string) {
  if (currentQuestion.value) {
    answers.value[currentQuestion.value.id] = value
    saveStatus.value = 'unsaved'
    // Also save to localStorage immediately
    saveToLocalStorage()
  }
}

async function resumePractice() {
  if (serverSession.value) {
    loadFromServerSession()
  } else {
    loadFromLocalStorage()
  }
  showResumeDialog.value = false
  startTimer()
}

async function restartPractice() {
  // Delete server session
  if (authStore.token) {
    try {
      await deletePaperSession(authStore.token, paperId)
    } catch {}
  }
  // Clear local storage
  clearAll()
  // Reset state
  if (paper.value) {
    for (const q of paper.value.questions) {
      answers.value[q.id] = ''
    }
  }
  currentIndex.value = 0
  timerSeconds.value = 0
  showResumeDialog.value = false
  startTimer()
}

onMounted(async () => {
  await loadPaper()
  // Check for resume query parameter
  const shouldResume = route.query.resume === '1'
  if (shouldResume) {
    // Auto resume without dialog
    await resumePractice()
  } else {
    // Check for saved session
    const hasServer = await checkServerSession()
    if (hasServer) {
      showResumeDialog.value = true
    } else {
      startTimer()
    }
  }
  // Auto-save to server every 60 seconds
  autoSaveInterval = setInterval(() => {
    if (saveStatus.value === 'unsaved') {
      void saveToServer()
    }
  }, 60000)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
  if (autoSaveInterval) clearInterval(autoSaveInterval)
  // Save on leave
  void saveToServer()
})
</script>

<template>
  <div class="practice-page">
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- Resume Dialog -->
    <div v-else-if="showResumeDialog" class="resume-overlay">
      <div class="resume-dialog">
        <div class="resume-icon">
          <AppIcon name="document" :size="32" />
        </div>
        <h2>发现未完成的练习</h2>
        <p>你之前在这套试卷上有未完成的答案，是否继续？</p>
        <div class="resume-actions">
          <button type="button" class="resume-btn resume-btn-secondary" @click="restartPractice">
            重新开始
          </button>
          <button type="button" class="resume-btn resume-btn-primary" @click="resumePractice">
            继续练习
          </button>
        </div>
      </div>
    </div>

    <template v-else-if="paper">
      <!-- Top Bar -->
      <header class="topbar">
        <button type="button" class="back-btn" @click="router.push('/papers')">
          <AppIcon name="chevron-right" :size="14" style="transform: rotate(180deg)" />
          退出
        </button>
        <div class="topbar-center">
          <span class="topbar-badge">{{ currentIndex + 1 }}/{{ totalQuestions }}</span>
          <span class="topbar-type">{{ currentQuestion?.question_type || '综合题' }}</span>
        </div>
        <div class="topbar-right">
          <span class="topbar-save" :class="saveStatus">
            <template v-if="saveStatus === 'saved'">已保存</template>
            <template v-else-if="saveStatus === 'saving'">保存中...</template>
            <template v-else>未保存</template>
          </span>
          <span class="topbar-sep">|</span>
          <span class="topbar-timer">
            <AppIcon name="info" :size="12" />
            {{ formatTime(timerSeconds) }}
          </span>
          <span class="topbar-sep">|</span>
          <span class="topbar-stat">已答 {{ answeredCount }}</span>
        </div>
      </header>

      <!-- Content -->
      <main class="content">
        <!-- Requirement -->
        <div class="section requirement-section">
          <div class="section-body">
            <pre class="requirement-text">{{ currentQuestion?.requirement || '暂无要求' }}</pre>
          </div>
          <button
            v-if="currentMaterials.length > 0"
            type="button"
            class="toggle-btn"
            @click="showMaterials = !showMaterials"
          >
            <AppIcon name="document" :size="14" />
            {{ showMaterials ? '收起材料' : '查看材料 (' + currentMaterials.length + ')' }}
            <AppIcon name="chevron-right" :size="12" :class="{ rotated: showMaterials }" />
          </button>
        </div>

        <!-- Materials (collapsible) -->
        <div v-if="showMaterials && currentMaterials.length > 0" class="section materials-section">
          <div class="section-body materials-body">
            <div v-for="m in currentMaterials" :key="m.id" class="material-block">
              <div class="material-label">材料 {{ m.material_num }}</div>
              <pre class="material-text">{{ m.content }}</pre>
            </div>
          </div>
        </div>

        <!-- Answer -->
        <div class="answer-section">
          <div class="answer-header">
            <span class="answer-label">你的答案</span>
            <span class="answer-words">{{ wordCount }} 字</span>
          </div>
          <textarea
            :value="currentAnswer"
            @input="updateAnswer($event.target.value)"
            @blur="saveToServer"
            class="answer-input"
            placeholder="在此输入你的答案..."
          ></textarea>
        </div>
      </main>

      <!-- Bottom Bar -->
      <footer class="bottombar">
        <button type="button" class="nav-btn" @click="goToQuestion(currentIndex - 1)" :disabled="currentIndex === 0">
          <AppIcon name="chevron-right" :size="14" style="transform: rotate(180deg)" />
          上一题
        </button>
        <div class="dots">
          <span
            v-for="(q, index) in paper.questions"
            :key="q.id"
            class="dot"
            :class="{ active: index === currentIndex, done: answers[q.id]?.trim() }"
            @click="goToQuestion(index)"
          ></span>
        </div>
        <button
          v-if="currentIndex < totalQuestions - 1"
          type="button"
          class="nav-btn nav-btn-primary"
          @click="goToQuestion(currentIndex + 1)"
        >
          下一题
          <AppIcon name="chevron-right" :size="14" />
        </button>
        <button v-else type="button" class="nav-btn nav-btn-primary">
          提交全部
        </button>
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

.loading-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
}

/* Top Bar */
.topbar {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 44px;
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
}
.back-btn:hover { color: var(--accent); }

.topbar-center { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; }
.topbar-badge { padding: 2px 10px; background: var(--accent); color: #fff; font-size: 12px; font-weight: 700; border-radius: 100px; }
.topbar-type { font-size: 13px; color: var(--muted); }

.topbar-right { display: flex; align-items: center; gap: 8px; }
.topbar-timer { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
.topbar-stat { font-size: 12px; color: var(--support); }
.topbar-sep { color: var(--line); font-size: 12px; }
.topbar-save { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 100px; }
.topbar-save.saved { color: #166534; background: #dcfce7; }
.topbar-save.saving { color: #854d0e; background: #fef9c3; }
.topbar-save.unsaved { color: #92400e; background: #fef3c7; }

/* Content */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Section */
.section {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.section-body { padding: 16px; }

.requirement-text {
  font-size: 15px;
  color: var(--ink);
  line-height: 1.8;
  white-space: pre-wrap;
  margin: 0;
  font-family: inherit;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px;
  background: var(--bg-soft);
  border: none;
  border-top: 1px solid var(--line-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.toggle-btn:hover { color: var(--accent); }
.toggle-btn .rotated { transform: rotate(90deg); }

/* Materials */
.materials-section {
  max-height: 50vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.materials-body {
  overflow-y: auto;
  max-height: 50vh;
}

.material-block { margin-bottom: 16px; }
.material-block:last-child { margin-bottom: 0; }
.material-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--support);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
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
  min-height: 200px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.answer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--line-soft);
  flex-shrink: 0;
}

.answer-label { font-size: 13px; font-weight: 600; color: var(--ink); }
.answer-words { font-size: 13px; font-weight: 500; color: var(--support); font-variant-numeric: tabular-nums; }

.answer-input {
  flex: 1;
  width: 100%;
  min-height: 200px;
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
.answer-input::placeholder { color: var(--support); }

/* Bottom Bar */
.bottombar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--paper);
  border-top: 1px solid var(--line);
  flex-shrink: 0;
}

.dots { display: flex; align-items: center; gap: 6px; }
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--line);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.dot:hover { background: var(--line-strong); }
.dot.active { background: var(--accent); width: 20px; border-radius: 4px; }
.dot.done { background: #86efac; }

.nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--ink);
}
.nav-btn:hover:not(:disabled) { border-color: var(--line-strong); }
.nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.nav-btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.nav-btn-primary:hover:not(:disabled) { background: var(--accent-deep); }

@media (max-width: 768px) {
  .topbar-type { display: none; }
}

/* Resume Dialog */
.resume-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.resume-dialog {
  background: var(--paper);
  border-radius: var(--radius-xl);
  padding: 32px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: var(--shadow-xl);
}

.resume-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.resume-dialog h2 {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 8px;
}

.resume-dialog p {
  font-size: 14px;
  color: var(--muted);
  margin: 0 0 24px;
  line-height: 1.5;
}

.resume-actions {
  display: flex;
  gap: 12px;
}

.resume-btn {
  flex: 1;
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.resume-btn-secondary {
  background: var(--bg-soft);
  color: var(--ink);
  border: 1px solid var(--line);
}
.resume-btn-secondary:hover { background: var(--bg); }

.resume-btn-primary {
  background: var(--accent);
  color: #fff;
}
.resume-btn-primary:hover { background: var(--accent-deep); }
</style>
