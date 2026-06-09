<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { getLibraryFilters, listLibraryItems } from '@/modules/library/services/library.service'
import type { LibraryItem, LibraryItemTypeFilter } from '@/modules/library/types/library'

const router = useRouter()

const items = ref<LibraryItem[]>([])
const loading = ref(true)
const total = ref(0)
const activeScope = ref<'system' | 'user'>('system')
const activeType = ref<LibraryItemTypeFilter>('all')

const regions = ref<string[]>([])
const years = ref<number[]>([])
const difficulties = ref<string[]>([])
const questionTypes = ref<string[]>([])

const selectedRegion = ref('')
const selectedYear = ref('')
const selectedDifficulty = ref('')
const selectedQuestionType = ref('')

const headerMetaLabel = computed(() => {
  if (activeType.value === 'paper') return '套卷'
  if (activeType.value === 'question') return '单题'
  return '条题库内容'
})

const pageSubtitle = computed(() => {
  if (activeType.value === 'paper') return '选择套卷，开始整套练习'
  if (activeType.value === 'question') return '选择独立题，开始单题练习'
  return '混合浏览套卷和独立单题，按训练目标进入练习'
})

const canFilterQuestionType = computed(() => activeType.value !== 'paper' && questionTypes.value.length > 0)
const hasFilters = computed(() => Boolean(
  selectedRegion.value || selectedYear.value || selectedDifficulty.value || selectedQuestionType.value,
))

async function fetchFilters() {
  try {
    const res = await getLibraryFilters(authStore.token || '', activeScope.value)
    regions.value = res.regions
    years.value = res.years
    difficulties.value = res.difficulties
    questionTypes.value = res.question_types
  } catch (error) {
    console.error('Failed to fetch library filters:', error)
  }
}

async function fetchItems() {
  loading.value = true
  try {
    const res = await listLibraryItems(authStore.token || '', {
      item_type: activeType.value,
      scope: activeScope.value,
      region: selectedRegion.value || undefined,
      difficulty: selectedDifficulty.value || undefined,
      year: selectedYear.value ? Number(selectedYear.value) : undefined,
      question_type: selectedQuestionType.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('Failed to fetch library items:', error)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function switchScope(scope: 'system' | 'user') {
  activeScope.value = scope
  clearFilters()
  void fetchFilters()
}

function switchType(type: LibraryItemTypeFilter) {
  activeType.value = type
  if (type === 'paper') selectedQuestionType.value = ''
}

function toggleRegion(region: string) { selectedRegion.value = selectedRegion.value === region ? '' : region }
function toggleYear(year: number) { selectedYear.value = selectedYear.value === String(year) ? '' : String(year) }
function toggleDifficulty(difficulty: string) { selectedDifficulty.value = selectedDifficulty.value === difficulty ? '' : difficulty }
function toggleQuestionType(questionType: string) { selectedQuestionType.value = selectedQuestionType.value === questionType ? '' : questionType }
function clearFilters() { selectedRegion.value = ''; selectedYear.value = ''; selectedDifficulty.value = ''; selectedQuestionType.value = '' }

function getDiffClass(difficulty: string | null) {
  if (!difficulty) return ''
  if (difficulty === '简单') return 'easy'
  if (difficulty === '中等' || difficulty === '进阶') return 'medium'
  if (difficulty === '困难' || difficulty === '冲刺') return 'hard'
  return ''
}

function getItemIcon(item: LibraryItem) {
  return item.item_type === 'paper' ? 'library' : 'document'
}

function getItemTypeLabel(item: LibraryItem) {
  return item.item_type === 'paper' ? '套卷' : '单题'
}

function getItemMeta(item: LibraryItem) {
  if (item.item_type === 'paper') {
    return `${item.question_count ?? 0} 道小题`
  }
  const parts = [item.question_type, item.suggested_minutes ? `建议 ${item.suggested_minutes} 分钟` : null]
  return parts.filter(Boolean).join(' · ') || '独立练习题'
}

function openAction(path: string | undefined) {
  if (!path) return
  router.push(path)
}

watch([activeScope, activeType, selectedRegion, selectedYear, selectedDifficulty, selectedQuestionType], () => {
  void fetchItems()
})

onMounted(async () => {
  await fetchFilters()
  await fetchItems()
})
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <div>
        <h1>题库</h1>
        <p>{{ pageSubtitle }}</p>
      </div>
      <div class="header-meta">
        <span class="meta-val">{{ total }}</span>
        <span class="meta-lbl">{{ headerMetaLabel }}</span>
      </div>
    </header>

    <div class="scope-tabs">
      <button type="button" class="scope-tab" :class="{ active: activeScope === 'system' }" @click="switchScope('system')">
        <AppIcon name="library" :size="14" />
        系统题库
      </button>
      <button type="button" class="scope-tab" :class="{ active: activeScope === 'user' }" @click="switchScope('user')">
        <AppIcon name="user" :size="14" />
        我的题库
      </button>
    </div>

    <div class="type-tabs">
      <button type="button" class="type-tab" :class="{ active: activeType === 'all' }" @click="switchType('all')">全部</button>
      <button type="button" class="type-tab" :class="{ active: activeType === 'paper' }" @click="switchType('paper')">套卷练习</button>
      <button type="button" class="type-tab" :class="{ active: activeType === 'question' }" @click="switchType('question')">单题练习</button>
    </div>

    <div v-if="regions.length > 0 || years.length > 0 || difficulties.length > 0 || canFilterQuestionType" class="filter-bar">
      <div v-if="regions.length > 0" class="filter-row">
        <span class="filter-label">地区</span>
        <button v-for="region in regions" :key="region" type="button" class="chip" :class="{ active: selectedRegion === region }" @click="toggleRegion(region)">{{ region }}</button>
      </div>
      <div v-if="years.length > 0" class="filter-row">
        <span class="filter-label">年份</span>
        <button v-for="year in years" :key="year" type="button" class="chip" :class="{ active: selectedYear === String(year) }" @click="toggleYear(year)">{{ year }}</button>
      </div>
      <div v-if="difficulties.length > 0" class="filter-row">
        <span class="filter-label">难度</span>
        <button v-for="difficulty in difficulties" :key="difficulty" type="button" class="chip" :class="{ active: selectedDifficulty === difficulty }" @click="toggleDifficulty(difficulty)">{{ difficulty }}</button>
      </div>
      <div v-if="canFilterQuestionType" class="filter-row">
        <span class="filter-label">题型</span>
        <button v-for="questionType in questionTypes" :key="questionType" type="button" class="chip" :class="{ active: selectedQuestionType === questionType }" @click="toggleQuestionType(questionType)">{{ questionType }}</button>
      </div>
      <button v-if="hasFilters" type="button" class="chip clear" @click="clearFilters">清空筛选</button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="items.length === 0" class="empty">
      <div class="empty-icon"><AppIcon name="document" :size="28" /></div>
      <h3>{{ activeScope === 'system' ? '暂无系统题库内容' : '暂无个人题库内容' }}</h3>
      <p>{{ activeType === 'paper' ? '当前没有可练习的套卷' : activeType === 'question' ? '当前没有独立单题' : '当前筛选条件下没有题库内容' }}</p>
      <button v-if="activeScope === 'user'" type="button" class="empty-btn">
        <AppIcon name="plus" :size="14" />
        创建题库内容
      </button>
    </div>

    <div v-else class="library-grid">
      <article v-for="item in items" :key="item.item_key" class="library-card" :class="`is-${item.item_type}`">
        <div class="card-head">
          <div class="card-tags">
            <span class="type-tag"><AppIcon :name="getItemIcon(item)" :size="12" />{{ getItemTypeLabel(item) }}</span>
            <span v-if="item.region" class="tag">{{ item.region }}</span>
            <span v-if="item.year" class="tag">{{ item.year }}</span>
          </div>
          <span v-if="item.difficulty" class="diff" :class="getDiffClass(item.difficulty)">{{ item.difficulty }}</span>
        </div>

        <h3 class="card-title">{{ item.title }}</h3>
        <p v-if="item.source || item.tags.length > 0" class="card-source">
          {{ item.source || item.tags.slice(0, 2).join(' · ') }}
        </p>

        <div class="card-foot">
          <span class="card-count">{{ getItemMeta(item) }}</span>
          <div class="card-actions">
            <button v-if="item.secondary_action" type="button" class="card-btn card-btn-secondary" @click.stop="openAction(item.secondary_action?.path)">
              {{ item.secondary_action.label }}
            </button>
            <button type="button" class="card-btn" @click.stop="openAction(item.primary_action.path)">
              {{ item.primary_action.label }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}
.page-header h1 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0 0 4px; }
.page-header p { font-size: 13px; color: var(--muted); margin: 0; }
.header-meta { display: flex; align-items: baseline; gap: 4px; padding-top: 4px; }
.meta-val { font-size: 20px; font-weight: 700; color: var(--ink); font-family: var(--font-serif); }
.meta-lbl { font-size: 12px; color: var(--support); }

.scope-tabs,
.type-tabs {
  display: flex;
  gap: 4px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 4px;
}

.scope-tab,
.type-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.type-tab { font-size: 13px; }
.scope-tab:hover,
.type-tab:hover { color: var(--ink); background: var(--bg-soft); }
.scope-tab.active,
.type-tab.active { color: var(--accent); background: var(--accent-soft); font-weight: 600; }

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px 16px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.filter-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.filter-label { font-size: 11px; font-weight: 600; color: var(--support); text-transform: uppercase; letter-spacing: 0.04em; margin-right: 2px; }

.chip {
  padding: 4px 12px;
  border: 1px solid var(--line);
  border-radius: 100px;
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.chip:hover { border-color: var(--line-strong); color: var(--ink); }
.chip.active { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.chip.clear { border-color: var(--danger); color: var(--danger); }
.chip.clear:hover { background: var(--danger-soft); }

.loading-state { text-align: center; padding: 72px 24px; color: var(--support); font-size: 13px; }

.empty { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 72px 24px; background: var(--paper); border: 1px dashed var(--line-strong); border-radius: var(--radius-xl); }
.empty-icon { width: 56px; height: 56px; border-radius: 14px; background: var(--bg-soft); display: flex; align-items: center; justify-content: center; color: var(--support); margin-bottom: 16px; }
.empty h3 { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.empty p { font-size: 13px; color: var(--muted); margin: 0 0 16px; }

.empty-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.empty-btn:hover { background: var(--accent-deep); }

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.library-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
}
.library-card:hover { border-color: var(--accent); box-shadow: var(--shadow-md); }
.library-card.is-question { border-style: dashed; }

.card-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.card-tags { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.type-tag,
.tag { padding: 2px 8px; background: var(--accent-soft); color: var(--accent); font-size: 11px; font-weight: 600; border-radius: 100px; }
.type-tag { display: inline-flex; align-items: center; gap: 4px; background: var(--bg-soft); color: var(--ink); }
.is-question .type-tag { background: #eef2ff; color: #3730a3; }
.diff { padding: 2px 8px; font-size: 11px; font-weight: 600; border-radius: 100px; white-space: nowrap; }
.diff.easy { background: #dcfce7; color: #166534; }
.diff.medium { background: #fef9c3; color: #854d0e; }
.diff.hard { background: #fee2e2; color: #991b1b; }

.card-title { font-size: 14px; font-weight: 600; color: var(--ink); margin: 0; line-height: 1.5; flex: 1; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-source { font-size: 12px; color: var(--support); margin: -2px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: auto; }
.card-count { font-size: 12px; color: var(--support); }
.card-actions { display: flex; gap: 6px; flex-shrink: 0; }

.card-btn {
  padding: 6px 14px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.card-btn:hover { background: var(--accent-deep); }
.card-btn-secondary { background: var(--paper); color: var(--accent); border: 1px solid var(--accent); }
.card-btn-secondary:hover { background: var(--accent-soft); }

@media (max-width: 768px) {
  .page-content { padding: 20px; }
  .library-grid { grid-template-columns: 1fr; }
  .card-foot { align-items: flex-start; flex-direction: column; }
}
</style>
