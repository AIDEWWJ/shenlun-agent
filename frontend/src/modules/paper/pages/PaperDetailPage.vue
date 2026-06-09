<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { getPaperDetail } from '../services/paper.service'
import type { PaperDetail, PaperMaterial } from '../types/paper'

const route = useRoute()
const router = useRouter()
const paper = ref<PaperDetail | null>(null)
const loading = ref(true)
const expandedMaterial = ref<number | null>(null)

const paperId = Number(route.params.paperId)

async function fetchPaper() {
  loading.value = true
  try {
    paper.value = await getPaperDetail(authStore.token || '', paperId)
  } catch (e) {
    console.error('Failed to fetch paper:', e)
  } finally {
    loading.value = false
  }
}

function getMaterialByRefs(refs: string | null): PaperMaterial[] {
  if (!refs || !paper.value) return []
  const nums = refs.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
  return paper.value.materials.filter(m => nums.includes(m.material_num))
}

function startPractice(questionId: number) {
  router.push(`/practice/${questionId}`)
}

function toggleMaterial(num: number) {
  expandedMaterial.value = expandedMaterial.value === num ? null : num
}

function getDiffClass(d: string | null) {
  if (!d) return ''
  if (d === '简单') return 'easy'
  if (d === '中等') return 'medium'
  if (d === '困难') return 'hard'
  return ''
}

onMounted(() => { void fetchPaper() })
</script>

<template>
  <div class="page-content">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- Not found -->
    <div v-else-if="!paper" class="empty">
      <div class="empty-icon"><AppIcon name="document" :size="28" /></div>
      <h3>试卷不存在</h3>
      <button type="button" class="back-btn" @click="router.push('/papers')">返回题库</button>
    </div>

    <!-- Paper detail -->
    <template v-else>
      <header class="page-header">
        <div class="header-left">
          <button type="button" class="back-link" @click="router.push('/papers')">
            <AppIcon name="chevron-right" :size="14" style="transform: rotate(180deg)" />
            返回题库
          </button>
          <div class="header-info">
            <div class="header-tags">
              <span v-if="paper.region" class="tag">{{ paper.region }}</span>
              <span v-if="paper.difficulty" class="diff-tag" :class="getDiffClass(paper.difficulty)">{{ paper.difficulty }}</span>
              <span v-if="paper.year" class="year-tag">{{ paper.year }}年</span>
            </div>
            <h1>{{ paper.title }}</h1>
            <p class="header-meta">{{ paper.materials.length }} 篇材料 · {{ paper.question_count }} 道小题</p>
          </div>
        </div>
      </header>

      <!-- Materials section -->
      <section v-if="paper.materials.length > 0" class="section">
        <div class="section-title">
          <div class="section-icon"><AppIcon name="document" :size="16" /></div>
          <h2>阅读材料</h2>
        </div>
        <div class="materials-list">
          <div
            v-for="m in paper.materials"
            :key="m.id"
            class="material-card"
            :class="{ expanded: expandedMaterial === m.material_num }"
            @click="toggleMaterial(m.material_num)"
          >
            <div class="material-head">
              <span class="material-num">材料 {{ m.material_num }}</span>
              <span class="material-chars">{{ m.content.length }} 字</span>
              <AppIcon :name="expandedMaterial === m.material_num ? 'chevron-right' : 'chevron-right'" :size="14" class="material-arrow" :class="{ open: expandedMaterial === m.material_num }" />
            </div>
            <div v-if="expandedMaterial === m.material_num" class="material-body">
              <p>{{ m.content }}</p>
            </div>
            <div v-else class="material-preview">
              <p>{{ m.content.substring(0, 100) }}...</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Questions list -->
      <section class="section">
        <div class="section-title">
          <div class="section-icon accent"><AppIcon name="edit" :size="16" /></div>
          <h2>题目列表</h2>
        </div>
        <div class="questions-list">
          <div
            v-for="(q, index) in paper.questions"
            :key="q.id"
            class="question-card"
          >
            <div class="q-number">{{ index + 1 }}</div>
            <div class="q-content">
              <div class="q-head">
                <span v-if="q.question_type" class="q-type">{{ q.question_type }}</span>
                <span v-if="q.difficulty" class="q-diff" :class="getDiffClass(q.difficulty)">{{ q.difficulty }}</span>
                <span v-if="q.material_refs" class="q-refs">材料{{ q.material_refs }}</span>
              </div>
              <div v-if="q.requirement" class="q-requirement">{{ q.requirement }}</div>
            </div>
            <button type="button" class="q-practice-btn" @click="startPractice(q.id)">
              开始练习
            </button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading-state { text-align: center; padding: 72px 24px; color: var(--support); font-size: 13px; }

.empty { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 72px 24px; }
.empty-icon { width: 56px; height: 56px; border-radius: 14px; background: var(--bg-soft); display: flex; align-items: center; justify-content: center; color: var(--support); margin-bottom: 16px; }
.empty h3 { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 12px; }
.back-btn { padding: 8px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-md); font-size: 13px; font-weight: 600; cursor: pointer; }

/* Header */
.page-header { padding-bottom: 20px; border-bottom: 1px solid var(--line); }
.back-link { display: inline-flex; align-items: center; gap: 4px; background: none; border: none; color: var(--muted); font-size: 12px; cursor: pointer; margin-bottom: 12px; transition: color var(--transition-fast); }
.back-link:hover { color: var(--accent); }

.header-info { display: flex; flex-direction: column; gap: 8px; }
.header-tags { display: flex; align-items: center; gap: 8px; }
.tag { padding: 3px 10px; background: var(--accent-soft); color: var(--accent); font-size: 11px; font-weight: 600; border-radius: 100px; }
.diff-tag { padding: 3px 10px; font-size: 11px; font-weight: 600; border-radius: 100px; }
.diff-tag.easy { background: #dcfce7; color: #166534; }
.diff-tag.medium { background: #fef9c3; color: #854d0e; }
.diff-tag.hard { background: #fee2e2; color: #991b1b; }
.year-tag { padding: 3px 10px; background: var(--bg-soft); color: var(--muted); font-size: 11px; font-weight: 600; border-radius: 100px; }

.page-header h1 { font-size: 22px; font-weight: 700; color: var(--ink); margin: 0; line-height: 1.4; }
.header-meta { font-size: 13px; color: var(--muted); margin: 0; }

/* Section */
.section { display: flex; flex-direction: column; gap: 14px; }
.section-title { display: flex; align-items: center; gap: 10px; }
.section-icon { width: 32px; height: 32px; border-radius: 8px; background: var(--bg-soft); color: var(--muted); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.section-icon.accent { background: var(--accent-soft); color: var(--accent); }
.section-title h2 { font-size: 16px; font-weight: 600; color: var(--ink); margin: 0; }

/* Materials */
.materials-list { display: flex; flex-direction: column; gap: 10px; }

.material-card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.material-card:hover { border-color: var(--line-strong); }
.material-card.expanded { border-color: var(--accent); }

.material-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-soft);
}
.material-num { font-size: 13px; font-weight: 600; color: var(--ink); }
.material-chars { font-size: 11px; color: var(--support); margin-left: auto; }
.material-arrow { color: var(--support); transition: transform var(--transition-fast); }
.material-arrow.open { transform: rotate(90deg); }

.material-preview { padding: 0 16px 12px; }
.material-preview p { font-size: 12px; color: var(--muted); line-height: 1.6; margin: 0; }

.material-body { padding: 0 16px 16px; }
.material-body p { font-size: 13px; color: var(--ink); line-height: 1.8; margin: 0; white-space: pre-wrap; }

/* Questions */
.questions-list { display: flex; flex-direction: column; gap: 12px; }

.question-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
}

.q-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-soft);
  color: var(--ink);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.q-content { flex: 1; min-width: 0; }
.q-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.q-type { padding: 2px 8px; background: var(--accent-soft); color: var(--accent); font-size: 11px; font-weight: 600; border-radius: 100px; }
.q-diff { padding: 2px 8px; font-size: 11px; font-weight: 600; border-radius: 100px; }
.q-diff.easy { background: #dcfce7; color: #166534; }
.q-diff.medium { background: #fef9c3; color: #854d0e; }
.q-diff.hard { background: #fee2e2; color: #991b1b; }
.q-refs { padding: 2px 8px; background: var(--bg-soft); color: var(--muted); font-size: 11px; font-weight: 500; border-radius: 100px; }

.q-requirement { font-size: 13px; color: var(--ink); line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }

.q-practice-btn {
  flex-shrink: 0;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  align-self: center;
}
.q-practice-btn:hover {
  background: var(--accent-deep);
}

@media (max-width: 768px) {
  .question-card { flex-direction: column; gap: 12px; }
  .q-action { align-self: flex-end; }
}
</style>
