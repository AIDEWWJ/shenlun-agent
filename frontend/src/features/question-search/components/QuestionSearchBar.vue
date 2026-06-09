<script setup lang="ts">
defineProps<{
  keyword: string
  category: string
  categories: readonly string[]
  totalCount: number
}>()

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:category': [value: string]
}>()

function updateKeyword(event: Event) {
  emit('update:keyword', (event.target as HTMLInputElement).value)
}

function updateCategory(event: Event) {
  emit('update:category', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <div class="flex flex-col md:flex-row md:items-end gap-4 w-full">
    <div class="flex flex-col gap-1.5 flex-1">
      <label class="text-xs font-semibold text-gray-500 uppercase tracking-widest" for="question-keyword">搜索题目</label>
      <input
        id="question-keyword"
        :value="keyword"
        class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-md text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8b5a2b]/20 focus:border-[#8b5a2b] transition-colors"
        placeholder="按题目、主题、关键词检索"
        @input="updateKeyword"
      />
    </div>

    <div class="flex flex-col gap-1.5 w-full md:w-48">
      <label for="question-category" class="text-xs font-semibold text-gray-500 uppercase tracking-widest">题目分类</label>
      <select 
        id="question-category" 
        :value="category" 
        class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-md text-sm text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8b5a2b]/20 focus:border-[#8b5a2b] transition-colors appearance-none cursor-pointer" 
        @change="updateCategory"
      >
        <option v-for="item in categories" :key="item" :value="item">
          {{ item }}
        </option>
      </select>
    </div>

    <div class="flex flex-col gap-1.5 shrink-0">
      <label class="text-xs font-semibold text-gray-500 uppercase tracking-widest">当前结果</label>
      <div class="flex items-center px-4 py-2.5 bg-[rgba(139,90,43,0.08)] text-[#313742] font-medium border border-[#e5e7eb] rounded-md text-sm h-[42px] whitespace-nowrap">
        {{ totalCount }} 条匹配结果
      </div>
    </div>
  </div>
</template>
