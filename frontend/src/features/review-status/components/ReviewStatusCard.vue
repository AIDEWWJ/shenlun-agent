<script setup lang="ts">
import { RouterLink } from 'vue-router'

withDefaults(
  defineProps<{
    title: string
    summary: string
    status: 'draft' | 'completed' | 'queued'
    updatedAt: string
    score?: number | null
    actionLabel?: string
    actionTo?: string
  }>(),
  {
    score: null,
    actionLabel: '',
    actionTo: '',
  },
)

const statusToneMap = {
  draft: 'warning',
  completed: 'success',
  queued: 'accent',
} as const

const statusLabelMap = {
  draft: '草稿',
  completed: '已批改',
  queued: '待查看',
} as const
</script>

<template>
  <article class="summary-card review-status-card">
    <div class="question-card-head">
      <div>
        <strong>{{ title }}</strong>
        <p class="muted-text">{{ summary }}</p>
      </div>
      <span class="status-badge" :class="`is-${statusToneMap[status]}`">{{ statusLabelMap[status] }}</span>
    </div>

    <div class="question-meta-grid">
      <span>更新时间：{{ updatedAt }}</span>
      <span v-if="score !== null">总分：{{ score }}</span>
      <span v-else>尚未生成分数</span>
    </div>

    <RouterLink v-if="actionLabel && actionTo" :to="actionTo" class="text-link-button">
      {{ actionLabel }}
    </RouterLink>
  </article>
</template>
