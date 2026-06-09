<script setup lang="ts">
import type { ReportDimension } from '@/modules/review/types/review'

defineProps<{
  dimensions: ReportDimension[]
}>()
</script>

<template>
  <section class="space-y-4">
    <article v-for="dimension in dimensions" :key="dimension.name" class="bg-[#faf9f6] border border-stone-200 rounded p-5">
      <div class="flex justify-between items-baseline mb-3">
        <strong class="text-sm font-bold text-slate-800">{{ dimension.name }}</strong>
        <span class="text-sm font-serif font-bold text-[#8b6540]">{{ dimension.score }} <span class="text-xs text-stone-500 font-sans font-medium">/ {{ dimension.maxScore }}</span></span>
      </div>
      <div class="w-full h-1.5 bg-stone-200 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-[#8b6540] rounded-full" :style="{ width: `${(dimension.score / dimension.maxScore) * 100}%` }"></div>
      </div>
      <p class="text-sm text-stone-600 leading-relaxed">{{ dimension.comment }}</p>
    </article>
  </section>
</template>
