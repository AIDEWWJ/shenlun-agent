<script setup lang="ts">
defineProps<{
  answerText: string
  referenceAnswer: string
  optimizedExample: string
}>()
</script>

<template>
  <section class="flex flex-col gap-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- User Answer -->
      <article class="bg-white border border-stone-200 rounded overflow-hidden flex flex-col">
        <div class="px-4 py-3 bg-stone-50 border-b border-stone-200 flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-stone-400"></span>
          <strong class="text-sm font-bold text-slate-800">当前作答</strong>
        </div>
        <div class="p-4 flex-1">
          <pre class="whitespace-pre-wrap font-serif text-[15px] text-stone-700 leading-relaxed m-0">{{ answerText || '无作答内容' }}</pre>
        </div>
      </article>

      <!-- Reference Answer -->
      <article class="bg-white border border-stone-200 rounded overflow-hidden flex flex-col">
        <div class="px-4 py-3 bg-[#faf9f6] border-b border-stone-200 flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
          <strong class="text-sm font-bold text-slate-800">参考答案</strong>
        </div>
        <div class="p-4 flex-1">
          <pre class="whitespace-pre-wrap font-serif text-[15px] text-stone-700 leading-relaxed m-0">{{ referenceAnswer || '无参考答案' }}</pre>
        </div>
      </article>

      <!-- Optimized Example -->
      <article class="bg-white border border-[#8b6540]/30 rounded overflow-hidden flex flex-col relative shadow-sm">
        <div class="absolute top-0 left-0 w-full h-0.5 bg-[#8b6540]"></div>
        <div class="px-4 py-3 bg-[#8b6540]/5 border-b border-[#8b6540]/10 flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-[#8b6540]"></span>
          <strong class="text-sm font-bold text-[#8b6540]">优化示例 (AI)</strong>
        </div>
        <div class="p-4 flex-1">
          <pre class="whitespace-pre-wrap font-serif text-[15px] text-stone-800 leading-relaxed m-0">{{ optimizedExample || '无优化示例' }}</pre>
        </div>
      </article>

    </div>
  </section>
</template>
