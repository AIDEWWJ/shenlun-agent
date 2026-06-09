<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
import { listPracticeRecords, toggleFavorite } from '../services/records.service'

const router = useRouter()

const records = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)

// Filters
const filterType = ref('')
const filterFavorite = ref<boolean | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

// Group records by paper_id
const groupedRecords = computed(() => {
  const groups: Record<number, any[]> = {}
  const standalone: any[] = []

  for (const record of records.value) {
    if (record.paper_id) {
      if (!groups[record.paper_id]) groups[record.paper_id] = []
      groups[record.paper_id].push(record)
    } else {
      standalone.push(record)
    }
  }

  return { groups, standalone }
})

async function fetchRecords() {
  if (!authStore.token) { router.push('/auth'); return }
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filterType.value) params.question_type = filterType.value
    if (filterFavorite.value !== null) params.is_favorite = filterFavorite.value

    const res = await listPracticeRecords(authStore.token, params)
    records.value = res?.items || []
    total.value = res?.total || 0
  } catch (err) {
    console.error('Failed to fetch records:', err)
  } finally {
    loading.value = false
  }
}

async function handleToggleFavorite(recordId: number, currentState: boolean) {
  if (!authStore.token) return
  try {
    await toggleFavorite(authStore.token, recordId, !currentState)
    const record = records.value.find(r => r.id === recordId)
    if (record) record.is_favorite = !currentState
  } catch (err) {
    console.error('Failed to toggle favorite:', err)
  }
}

function nextPage() { if (page.value < totalPages.value) { page.value++; fetchRecords() } }
function prevPage() { if (page.value > 1) { page.value--; fetchRecords() } }

function formatDate(s: string) {
  if (!s) return ''
  const d = new Date(s)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function getScoreColor(score: number | null) {
  if (score === null || score === undefined) return 'var(--support)'
  if (score >= 80) return '#166534'
  if (score >= 60) return '#854d0e'
  return '#991b1b'
}

onMounted(() => { fetchRecords() })
</script>

<template>
  <div class="history-page">
    <div class="shell">
      <!-- Header -->
      <header class="page-header">
        <div>
          <h1>练习记录</h1>
          <p class="page-desc">查看历史练习与 AI 批改报告</p>
        </div>
        <div class="header-meta">
          <span class="record-count">共 {{ total }} 条</span>
        </div>
      </header>

      <!-- Filters -->
      <div class="filter-bar">
        <button type="button" class="chip" :class="{ active: filterFavorite === true }" @click="filterFavorite = filterFavorite === true ? null : true; fetchRecords()">
          <AppIcon name="star" :size="12" /> 仅看收藏
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">加载中...</div>

      <!-- Empty -->
      <div v-else-if="records.length === 0" class="empty-state">
        <div class="empty-icon"><AppIcon name="history" :size="32" /></div>
        <h3>暂无练习记录</h3>
        <p>完成一次练习后，记录会显示在这里</p>
      </div>

      <!-- Records -->
      <template v-else>
        <!-- Paper Groups -->
        <div v-for="(items, paperId) in groupedRecords.groups" :key="paperId" class="paper-group">
          <div class="group-header">
            <AppIcon name="library" :size="16" />
            <span class="group-title">试卷练习 #{{ paperId }}</span>
            <span class="group-count">{{ items.length }} 题</span>
            <span class="group-date">{{ formatDate(items[0]?.created_at) }}</span>
          </div>
          <div class="group-items">
            <div v-for="(record, index) in items" :key="record.id" class="record-card">
              <div class="record-num">{{ index + 1 }}</div>
              <div class="record-info">
                <div class="record-title">{{ record.question_title || '题目' }}</div>
                <div class="record-meta">
                  <span v-if="record.question_type" class="record-type">{{ record.question_type }}</span>
                  <span class="record-date">{{ formatDate(record.created_at) }}</span>
                </div>
              </div>
              <div class="record-score" :style="{ color: getScoreColor(record.score) }">
                {{ record.score ?? '--' }}
              </div>
              <div class="record-actions">
                <button type="button" class="action-btn" :class="{ active: record.is_favorite }" @click="handleToggleFavorite(record.id, record.is_favorite)">
                  <AppIcon name="star" :size="14" />
                </button>
                <RouterLink :to="`/reports/${record.review_id}`" class="action-btn" v-if="record.review_id">
                  <AppIcon name="chevron-right" :size="14" />
                </RouterLink>
              </div>
            </div>
          </div>
        </div>

        <!-- Standalone Records -->
        <div v-if="groupedRecords.standalone.length > 0" class="paper-group">
          <div class="group-header">
            <AppIcon name="document" :size="16" />
            <span class="group-title">单题练习</span>
            <span class="group-count">{{ groupedRecords.standalone.length }} 题</span>
          </div>
          <div class="group-items">
            <div v-for="record in groupedRecords.standalone" :key="record.id" class="record-card">
              <div class="record-info">
                <div class="record-title">{{ record.question_title || '题目' }}</div>
                <div class="record-meta">
                  <span v-if="record.question_type" class="record-type">{{ record.question_type }}</span>
                  <span class="record-date">{{ formatDate(record.created_at) }}</span>
                </div>
              </div>
              <div class="record-score" :style="{ color: getScoreColor(record.score) }">
                {{ record.score ?? '--' }}
              </div>
              <div class="record-actions">
                <button type="button" class="action-btn" :class="{ active: record.is_favorite }" @click="handleToggleFavorite(record.id, record.is_favorite)">
                  <AppIcon name="star" :size="14" />
                </button>
                <RouterLink :to="`/reports/${record.review_id}`" class="action-btn" v-if="record.review_id">
                  <AppIcon name="chevron-right" :size="14" />
                </RouterLink>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Pagination -->
      <nav v-if="total > pageSize" class="pagination">
        <button type="button" :disabled="page === 1" class="page-btn" @click="prevPage">上一页</button>
        <span class="page-info">{{ page }} / {{ totalPages }}</span>
        <button type="button" :disabled="page >= totalPages" class="page-btn" @click="nextPage">下一页</button>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  background: var(--bg);
  min-height: 100%;
}

.shell {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 40px 64px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.page-header h1 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0 0 4px; }
.page-desc { font-size: 13px; color: var(--muted); margin: 0; }
.header-meta { display: flex; align-items: center; gap: 12px; }
.record-count { font-size: 13px; color: var(--support); }

/* Filters */
.filter-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
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

/* States */
.loading-state { text-align: center; padding: 72px 24px; color: var(--support); font-size: 13px; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 72px 24px;
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-xl);
}

.empty-icon { color: var(--support); margin-bottom: 16px; }
.empty-state h3 { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.empty-state p { font-size: 13px; color: var(--muted); margin: 0; }

/* Paper Groups */
.paper-group {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: var(--bg-soft);
  border-bottom: 1px solid var(--line-soft);
  color: var(--ink);
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
}

.group-count {
  font-size: 12px;
  color: var(--support);
  padding: 2px 8px;
  background: var(--paper);
  border-radius: 100px;
}

.group-date {
  font-size: 12px;
  color: var(--support);
}

.group-items {
  display: flex;
  flex-direction: column;
}

/* Record Card */
.record-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--line-soft);
  transition: background var(--transition-fast);
}
.record-card:last-child { border-bottom: none; }
.record-card:hover { background: var(--bg-soft); }

.record-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--bg-soft);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.record-info { flex: 1; min-width: 0; }
.record-title { font-size: 13px; font-weight: 500; color: var(--ink); margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.record-meta { display: flex; align-items: center; gap: 8px; }
.record-type { font-size: 11px; color: var(--accent); background: var(--accent-soft); padding: 1px 6px; border-radius: 100px; }
.record-date { font-size: 11px; color: var(--support); }

.record-score {
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-serif);
  flex-shrink: 0;
  min-width: 40px;
  text-align: center;
}

.record-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: 1px solid var(--line);
  background: var(--paper);
  color: var(--support);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
}
.action-btn:hover { color: var(--accent); border-color: var(--accent); }
.action-btn.active { color: var(--gold, #b45309); border-color: var(--gold, #b45309); }

/* Pagination */
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; padding-top: 12px; }
.page-btn { padding: 8px 16px; border: 1px solid var(--line); border-radius: var(--radius-lg); background: var(--paper); color: var(--ink); font-size: 13px; font-weight: 500; cursor: pointer; transition: all var(--transition-fast); }
.page-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-info { font-size: 13px; color: var(--muted); }

@media (max-width: 768px) {
  .shell { padding: 20px; }
  .record-score { font-size: 16px; }
}
</style>
