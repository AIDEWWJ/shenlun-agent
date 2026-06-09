<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name:
      | 'home'
      | 'library'
      | 'history'
      | 'settings'
      | 'info'
      | 'admin'
      | 'github'
      | 'login'
      | 'logout'
      | 'user'
      | 'document'
      | 'edit'
      | 'review'
      | 'report'
      | 'spark'
      | 'lock'
      | 'filter'
      | 'search'
      | 'chevron-right'
      | 'plus'
      | 'trash'
      | 'check'
      | 'star'
    size?: number
    stroke?: number
  }>(),
  {
    size: 18,
    stroke: 1.8,
  },
)

type IconName =
  | 'home'
  | 'library'
  | 'history'
  | 'settings'
  | 'info'
  | 'admin'
  | 'github'
  | 'login'
  | 'logout'
  | 'user'
  | 'document'
  | 'edit'
  | 'review'
  | 'report'
  | 'spark'
  | 'lock'
  | 'filter'
  | 'search'
  | 'chevron-right'
  | 'plus'
  | 'trash'
  | 'check'
  | 'star'

const iconPaths: Record<IconName, readonly string[]> = {
  home: ['M3 10.5L12 3l9 7.5', 'M5.5 9.5V20h13V9.5', 'M9.5 20v-5h5v5'],
  library: ['M4.5 5.5h6v14h-6z', 'M13.5 4.5h6v15h-6z', 'M6.5 8h2', 'M15.5 8h2'],
  history: ['M4 12a8 8 0 1 0 2.3-5.7', 'M4 4v4h4', 'M12 8v4l3 2'],
  settings: ['M12 8.2a3.8 3.8 0 1 0 0 7.6a3.8 3.8 0 1 0 0-7.6', 'M12 2.8v2.1', 'M12 19.1v2.1', 'M4.8 4.8l1.5 1.5', 'M17.7 17.7l1.5 1.5', 'M2.8 12h2.1', 'M19.1 12h2.1', 'M4.8 19.2l1.5-1.5', 'M17.7 6.3l1.5-1.5'],
  info: ['M12 10v6', 'M12 7.2h.01', 'M12 21a9 9 0 1 0 0-18a9 9 0 1 0 0 18z'],
  admin: ['M4 19.5v-1.2c0-2 1.7-3.6 3.7-3.6h8.6c2 0 3.7 1.6 3.7 3.6v1.2', 'M12 12.2a4 4 0 1 0 0-8a4 4 0 1 0 0 8', 'M18.5 6.5l2 2', 'M20.5 6.5l-2 2'],
  github: ['M9 18.5c-4 .9-4-2-5.7-2.4', 'M15 18.5c4 .9 4-2 5.7-2.4', 'M9 18.5v-3.2', 'M15 18.5v-3.2', 'M8.7 6.8c-.9-.3-1.7-1.7-.8-3.3', 'M15.3 6.8c.9-.3 1.7-1.7.8-3.3', 'M7.8 14.3c-2.2-.7-3.3-2.4-3.3-4.7c0-1.3.5-2.5 1.5-3.4c-.2-.6-.5-1.8.1-3.3c0 0 1.2-.4 3.9 1.5a13.2 13.2 0 0 1 7 0c2.7-1.9 3.9-1.5 3.9-1.5c.6 1.5.3 2.7.1 3.3c1 .9 1.5 2.1 1.5 3.4c0 2.3-1.1 4-3.3 4.7'],
  login: ['M13 5l7 7-7 7', 'M20 12H9', 'M11 4H5v16h6'],
  logout: ['M11 4H5v16h6', 'M13 5l7 7-7 7', 'M20 12H9'],
  user: ['M12 12a4 4 0 1 0 0-8a4 4 0 1 0 0 8', 'M4 20v-1.2c0-2.2 1.8-4 4-4h8c2.2 0 4 1.8 4 4V20'],
  document: ['M7 3.5h7l4 4V20H7z', 'M14 3.5V8h4', 'M9.5 12h5', 'M9.5 15.5h5'],
  edit: ['M4 20h4l10.5-10.5l-4-4L4 16v4', 'M12.5 5.5l4 4'],
  review: ['M4.5 6.5h15v11h-15z', 'M8 17.5h8', 'M8.2 10.8l2.2 2.2l5-5'],
  report: ['M6 4.5h12v15H6z', 'M9 9.5h6', 'M9 13h6', 'M9 16.5h4'],
  spark: ['M12 3l1.4 4.3L18 8.7l-4.6 1.4L12 14.5l-1.4-4.4L6 8.7l4.6-1.4L12 3', 'M18.5 15.5l.7 2.1l2.1.7l-2.1.7l-.7 2.1l-.7-2.1l-2.1-.7l2.1-.7l.7-2.1'],
  lock: ['M8 10.5V8a4 4 0 0 1 8 0v2.5', 'M5.5 10.5h13v10h-13z', 'M12 14v3'],
  filter: ['M3.5 5.5h17', 'M6 11.5h12', 'M9 17.5h6'],
  search: ['M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14', 'M20.5 20.5l-4.5-4.5'],
  'chevron-right': ['M9 5l7 7-7 7'],
  plus: ['M12 5v14', 'M5 12h14'],
  trash: ['M4 7h16', 'M10 11v6', 'M14 11v6', 'M6 7l1 13h10l1-13', 'M9 7V4h6v3'],
  check: ['M5 12.5l4.5 4.5l10-10'],
  star: ['M12 3l2.8 6l6.6.6l-5 4.5l1.5 6.5l-5.9-3.4l-5.9 3.4l1.5-6.5l-5-4.5l6.6-.6z'],
} as const

const paths = computed(() => iconPaths[props.name])
</script>

<template>
  <span class="app-icon" :style="{ width: `${size}px`, height: `${size}px` }" aria-hidden="true">
    <svg viewBox="0 0 24 24" fill="none" :stroke-width="stroke" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
      <path v-for="path in paths" :key="path" :d="path" />
    </svg>
  </span>
</template>
