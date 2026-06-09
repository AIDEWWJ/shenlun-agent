<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/>
      </svg>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-desc">{{ description }}</p>
    <RouterLink v-if="actionLabel && actionTo" :to="actionTo" class="empty-action">
      {{ actionLabel }}
      <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
    </RouterLink>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-xl);
}

@media (max-width: 640px) {
  .empty-state {
    padding: 32px 16px;
  }
}

.empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--bg-soft);
  color: var(--support);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 6px;
  font-family: var(--font-sans);
}

.empty-desc {
  font-size: 13px;
  color: var(--muted);
  max-width: 320px;
  margin-bottom: 20px;
}

.empty-action {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 18px;
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.empty-action:hover {
  background: var(--accent-hover);
}
</style>
