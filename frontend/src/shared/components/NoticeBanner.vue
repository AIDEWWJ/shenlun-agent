<script setup lang="ts">
defineProps<{
  message: string
  tone: 'success' | 'error'
}>()
</script>

<template>
  <p class="notice-box" :class="{ 'is-success': tone === 'success', 'is-error': tone === 'error' }">{{ message }}</p>
</template>
