<script setup lang="ts">
defineProps<{
  totalScore: number
  provider: string
  model: string
  overallComment: string
  strengths: string[]
  issues: string[]
}>()
</script>

<template>
  <section class="report-summary-panel">
    <div class="report-topbar">
      <div class="report-topbar-main">
        <p class="section-eyebrow">综合评估</p>
        <h2>总分与总评</h2>
        <p class="muted-text">{{ overallComment }}</p>
      </div>
      <div class="report-score-card">
        <span class="muted-text">总分</span>
        <strong>{{ totalScore }}</strong>
        <span>{{ provider }} / {{ model }}</span>
      </div>
    </div>

    <div class="summary-grid">
      <article class="summary-card">
        <strong>亮点</strong>
        <ul class="detail-list">
          <li v-for="item in strengths" :key="item">{{ item }}</li>
        </ul>
      </article>
      <article class="summary-card">
        <strong>问题</strong>
        <ul class="detail-list">
          <li v-for="item in issues" :key="item">{{ item }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>
