<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/shared/components/AppIcon.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { authStore } from '@/modules/auth/store'
import { listErrorNotebook, generateErrorNotebook, resolveEntry } from '../services/error-notebook.service'

const entries = ref<any[]>([])
const loading = ref(true)
const generating = ref(false)

async function fetchEntries() {
  if (!authStore.token) return
  loading.value = true
  try {
    const res = await listErrorNotebook(authStore.token)
    entries.value = res?.items || res || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (!authStore.token) return
  generating.value = true
  try {
    await generateErrorNotebook(authStore.token)
    await fetchEntries()
  } catch (err) {
    console.error(err)
  } finally {
    generating.value = false
  }
}

async function handleResolve(entryId: number) {
  if (!authStore.token) return
  try {
    await resolveEntry(authStore.token, entryId)
    const entry = entries.value.find(e => e.id === entryId)
    if (entry) entry.resolved = true
  } catch (err) {
    console.error(err)
  }
}

onMounted(() => { fetchEntries() })
</script>

<template>
  <div class="page shell">
    <header class="page-header">
      <div>
        <h1>错题本</h1>
        <p>AI 自动归纳你的薄弱点，帮助针对性提升</p>
      </div>
      <button type="button" class="gen-btn" :disabled="generating" @click="handleGenerate">
        <AppIcon name="spark" :size="14" />
        {{ generating ? '生成中...' : '重新生成' }}
      </button>
    </header>

    <div v-if="loading" class="skeleton-list">
      <div v-for="i in 3" :key="i" class="skeleton-card"></div>
    </div>

    <EmptyState
      v-else-if="entries.length === 0"
      title="暂无错题记录"
      description="完成更多练习后，AI 会自动归纳你的常见问题。"
      action-label="前往题库"
      action-to="/papers"
    />

    <div v-else class="entry-list">
      <article v-for="entry in entries" :key="entry.id" class="entry-card" :class="{ resolved: entry.resolved }">
        <div class="entry-main">
          <div class="entry-head">
            <span class="entry-type">{{ entry.question_type || entry.category || '综合' }}</span>
            <span v-if="entry.resolved" class="entry-resolved">
              <AppIcon name="check" :size="12" />
              已解决
            </span>
          </div>
          <h3 class="entry-title">{{ entry.title || entry.problem || '未命名问题' }}</h3>
          <p class="entry-desc">{{ entry.description || entry.suggestion || '' }}</p>
          <div v-if="entry.question_title" class="entry-source">
            来源：{{ entry.question_title }}
          </div>
        </div>
        <div class="entry-actions">
          <button v-if="!entry.resolved" type="button" class="resolve-btn" @click="handleResolve(entry.id)">
            <AppIcon name="check" :size="12" />
            标记已解决
          </button>
          <RouterLink v-if="entry.question_id" :to="`/practice/${entry.question_id}`" class="practice-link">
            去练习
            <AppIcon name="chevron-right" :size="12" />
          </RouterLink>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 32px 0 64px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 22px;
  font-weight: 700;
  font-family: var(--font-sans);
  color: var(--ink);
  margin-bottom: 4px;
}

.page-header p {
  font-size: 13px;
  color: var(--muted);
}

.gen-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.gen-btn:hover:not(:disabled) { background: var(--accent-deep); }
.gen-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.skeleton-list { display: flex; flex-direction: column; gap: 12px; }
.skeleton-card { height: 120px; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl); animation: pulse 2s ease infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.entry-list { display: flex; flex-direction: column; gap: 12px; }

.entry-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  transition: border-color var(--transition-fast);
}

.entry-card:hover { border-color: var(--line-strong); }
.entry-card.resolved { opacity: 0.6; }

.entry-main { flex: 1; min-width: 0; }

.entry-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }

.entry-type {
  padding: 3px 10px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  border-radius: 100px;
}

.entry-resolved {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--success);
  font-weight: 600;
}

.entry-title { font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 6px; }
.entry-desc { font-size: 13px; color: var(--muted); line-height: 1.6; margin-bottom: 8px; }
.entry-source { font-size: 12px; color: var(--support); }

.entry-actions { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }

.resolve-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--success);
  border-radius: var(--radius-md);
  background: var(--paper);
  color: var(--success);
  font-size: 12px;
  font-weight: 600;
}

.resolve-btn:hover { background: var(--success-soft); }

.practice-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  transition: all var(--transition-fast);
}

.practice-link:hover { border-color: var(--accent); color: var(--accent); }
</style>
