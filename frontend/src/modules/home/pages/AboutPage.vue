<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { platformHighlights, aboutCommitments } from '@/app/config/site'
</script>

<template>
  <div class="about-page">
    <div class="shell">
      <!-- Header -->
      <header class="about-header">
        <h1>关于平台</h1>
        <p class="about-subtitle">
          把训练放回一条路径里。练习、草稿和报告不再分散，每一次进步都被记录。
        </p>
      </header>

      <!-- Principles -->
      <section class="principles">
        <h2 class="section-title">设计原则</h2>
        <div class="principle-list">
          <article v-for="(item, index) in platformHighlights" :key="item.title" class="principle-item">
            <span class="principle-num">0{{ index + 1 }}</span>
            <div class="principle-body">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </div>
          </article>
        </div>
      </section>

      <!-- Commitments -->
      <section class="commitments">
        <h2 class="section-title">我们的承诺</h2>
        <div class="commitment-grid">
          <div v-for="item in aboutCommitments" :key="item.title" class="commitment-card">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta-section">
        <h2>准备好开始练习了吗？</h2>
        <RouterLink to="/papers" class="cta-btn">
          进入题库
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </RouterLink>
      </section>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  padding: 48px 0 80px;
}

.about-header {
  margin-bottom: 48px;
  max-width: 560px;
}

.about-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 12px;
}

.about-subtitle {
  font-size: 15px;
  color: var(--muted);
  line-height: 1.8;
}

/* Section Title */
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-sans);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

/* Principles */
.principles {
  margin-bottom: 48px;
}

.principle-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.principle-item {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.principle-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-serif);
  flex-shrink: 0;
  opacity: 0.6;
}

.principle-body h3 {
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 6px;
  font-family: var(--font-sans);
}

.principle-body p {
  font-size: 14px;
  color: var(--muted);
  line-height: 1.7;
}

/* Commitments */
.commitments {
  margin-bottom: 48px;
}

.commitment-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.commitment-card {
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
}

.commitment-card h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 8px;
  font-family: var(--font-sans);
}

.commitment-card p {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.6;
}

/* CTA */
.cta-section {
  text-align: center;
  padding: 48px 24px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.cta-section h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 20px;
  font-family: var(--font-sans);
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.cta-btn:hover {
  background: var(--accent-deep);
  box-shadow: var(--shadow-md);
}

/* Responsive */
@media (max-width: 768px) {
  .commitment-grid {
    grid-template-columns: 1fr;
  }

  .about-header h1 {
    font-size: 26px;
  }
}
</style>
