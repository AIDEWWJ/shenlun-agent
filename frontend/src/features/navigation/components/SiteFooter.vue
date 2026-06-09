<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <footer class="site-footer">
    <div class="shell footer-inner">
      <RouterLink to="/about" class="footer-link">关于</RouterLink>
      <span class="footer-dot">·</span>
      <RouterLink to="/papers" class="footer-link">题库</RouterLink>
      <span class="footer-dot">·</span>
      <span class="footer-copy">&copy; 2024 Shenlun Agent</span>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: 48px;
  padding: 16px 0;
  border-top: 1px solid var(--line);
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.footer-link {
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
  transition: color var(--transition-fast);
}

.footer-link:hover {
  color: var(--accent);
}

.footer-dot {
  color: var(--line-strong);
  font-size: 12px;
}

.footer-copy {
  font-size: 12px;
  color: var(--support);
}

@media (max-width: 640px) {
  .site-footer {
    margin-top: 32px;
    padding: 12px 0;
  }

  .footer-inner {
    gap: 8px;
  }

  .footer-link,
  .footer-dot,
  .footer-copy {
    font-size: 11px;
  }
}
</style>
