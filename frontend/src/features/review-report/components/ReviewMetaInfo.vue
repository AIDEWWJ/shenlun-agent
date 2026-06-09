<script setup lang="ts">
import type { PracticeReportRecord } from '@/modules/review/types/review'

defineProps<{
  report: PracticeReportRecord
}>()
</script>

<template>
  <section class="summary-card">
    <strong>报告信息</strong>
    <div class="detail-list">
      <p>题目：{{ report.questionTitle }}</p>
      <p>题型：{{ report.questionType }}</p>
      <p>来源：{{ report.source }}</p>
      <p>批改时间：{{ report.createdAt }}</p>
      <p>模型：{{ report.provider }} / {{ report.model }}</p>
    </div>
  </section>
</template>
