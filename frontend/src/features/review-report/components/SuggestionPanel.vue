<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    items: string[]
  }>(),
  {
    title: '改进建议',
  },
)
</script>

<template>
  <section class="summary-card">
    <strong>{{ title }}</strong>
    <ul class="detail-list">
      <li v-for="item in items" :key="item">{{ item }}</li>
    </ul>
  </section>
</template>
