<script setup lang="ts">
defineProps<{
  kicker: string
  title: string
  hint?: string
  compact?: boolean
}>()
</script>

<template>
  <div class="section-header" :class="{ compact: compact }">
    <div>
      <p class="panel-kicker">{{ kicker }}</p>
      <h2>{{ title }}</h2>
      <p v-if="hint" class="workspace-hint">{{ hint }}</p>
    </div>
  </div>
</template>
