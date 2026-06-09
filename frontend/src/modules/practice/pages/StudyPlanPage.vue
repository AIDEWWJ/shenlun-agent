<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { getStudyPlan, generateStudyPlan } from '../services/study-plan.service'

const plan = ref<any>(null)
const loading = ref(true)
const generating = ref(false)

async function fetchPlan() {
  if (!authStore.token) return
  loading.value = true
  try {
    const res = await getStudyPlan(authStore.token)
    plan.value = res
  } catch {} finally { loading.value = false }
}

async function handleGenerate() {
  if (!authStore.token) return
  generating.value = true
  try {
    const res = await generateStudyPlan(authStore.token)
    plan.value = res
  } catch (err) {
    console.error(err)
  } finally { generating.value = false }
}

onMounted(() => { fetchPlan() })
</script>

<template>
  <div class="page shell">
    <header class="page-header">
      <div>
        <h1>学习计划</h1>
        <p>AI 根据你的练习情况生成个性化学习建议</p>
      </div>
      <button type="button" class="gen-btn" :disabled="generating" @click="handleGenerate">
        <AppIcon name="spark" :size="14" />
        {{ generating ? '生成中...' : '重新生成' }}
      </button>
    </header>

    <div v-if="loading" class="skeleton-list">
      <div v-for="i in 3" :key="i" class="skeleton-card"></div>
    </div>

    <div v-else-if="!plan" class="empty-state">
      <div class="empty-icon">
        <AppIcon name="document" :size="24" />
      </div>
      <h3>暂无学习计划</h3>
      <p>点击「重新生成」让 AI 为你制定个性化学习计划</p>
      <button type="button" class="gen-btn" :disabled="generating" @click="handleGenerate">
        <AppIcon name="spark" :size="14" />
        生成学习计划
      </button>
    </div>

    <div v-else class="plan-content">
      <!-- Summary -->
      <section v-if="plan.summary || plan.overview" class="plan-card">
        <h3>总体建议</h3>
        <p class="plan-text">{{ plan.summary || plan.overview }}</p>
      </section>

      <!-- Tasks/Steps -->
      <section v-if="plan.tasks || plan.steps || plan.items" class="plan-card">
        <h3>学习任务</h3>
        <div class="task-list">
          <div v-for="(task, i) in (plan.tasks || plan.steps || plan.items)" :key="i" class="task-item">
            <span class="task-num">{{ i + 1 }}</span>
            <div class="task-body">
              <strong>{{ task.title || task.name || task }}</strong>
              <p v-if="task.description || task.detail">{{ task.description || task.detail }}</p>
              <RouterLink v-if="task.question_id" :to="`/practice/${task.question_id}`" class="task-link">
                去练习 <AppIcon name="chevron-right" :size="12" />
              </RouterLink>
            </div>
          </div>
        </div>
      </section>

      <!-- Weak areas -->
      <section v-if="plan.weak_areas || plan.weaknesses" class="plan-card">
        <h3>薄弱环节</h3>
        <div class="weak-list">
          <span v-for="(area, i) in (plan.weak_areas || plan.weaknesses)" :key="i" class="weak-tag">
            {{ typeof area === 'string' ? area : area.name || area.type }}
          </span>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 32px 0 64px; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h1 { font-size: 22px; font-weight: 700; font-family: var(--font-sans); color: var(--ink); margin-bottom: 4px; }
.page-header p { font-size: 13px; color: var(--muted); }

.gen-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; background: var(--accent); color: #fff;
  border: none; border-radius: var(--radius-md); font-size: 13px; font-weight: 600;
  transition: background var(--transition-fast); flex-shrink: 0;
}
.gen-btn:hover:not(:disabled) { background: var(--accent-deep); }
.gen-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.skeleton-list { display: flex; flex-direction: column; gap: 12px; }
.skeleton-card { height: 100px; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl); animation: pulse 2s ease infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.empty-state {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  padding: 64px 24px; background: var(--paper); border: 1px dashed var(--line-strong); border-radius: var(--radius-xl);
}
.empty-icon { width: 48px; height: 48px; border-radius: 12px; background: var(--bg-soft); color: var(--support); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.empty-state h3 { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 6px; font-family: var(--font-sans); }
.empty-state p { font-size: 13px; color: var(--muted); margin-bottom: 20px; }

.plan-content { display: flex; flex-direction: column; gap: 16px; }

.plan-card {
  padding: 24px; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl);
}
.plan-card h3 { font-size: 15px; font-weight: 600; color: var(--ink); font-family: var(--font-sans); margin-bottom: 12px; }
.plan-text { font-size: 14px; line-height: 1.8; color: var(--muted); }

.task-list { display: flex; flex-direction: column; gap: 12px; }
.task-item { display: flex; gap: 14px; align-items: flex-start; }
.task-num {
  width: 26px; height: 26px; border-radius: 7px; background: var(--accent-soft); color: var(--accent);
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.task-body strong { font-size: 14px; font-weight: 600; color: var(--ink); display: block; margin-bottom: 4px; }
.task-body p { font-size: 13px; color: var(--muted); line-height: 1.6; margin-bottom: 6px; }
.task-link { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 600; color: var(--accent); }

.weak-list { display: flex; flex-wrap: wrap; gap: 8px; }
.weak-tag {
  padding: 5px 14px; background: var(--danger-soft); color: var(--danger);
  font-size: 12px; font-weight: 600; border-radius: 100px;
}
</style>
