<script setup lang="ts">
import { RouterLink } from 'vue-router'

import AppIcon from '@/shared/components/AppIcon.vue'
import { authStore } from '@/modules/auth/store'
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <h1>后台总览</h1>
      <p>管理系统用户、AI 配置和邮件服务</p>
    </header>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon"><AppIcon name="user" :size="18" /></div>
        <div class="stat-info">
          <span class="stat-label">当前用户</span>
          <strong>{{ authStore.user?.username || '管理员' }}</strong>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon accent"><AppIcon name="admin" :size="18" /></div>
        <div class="stat-info">
          <span class="stat-label">权限</span>
          <strong>管理员</strong>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><AppIcon name="settings" :size="18" /></div>
        <div class="stat-info">
          <span class="stat-label">模块</span>
          <strong>用户 · AI · 邮件</strong>
        </div>
      </div>
    </div>

    <!-- Quick Links -->
    <div class="link-list">
      <RouterLink to="/papers" class="link-card">
        <div class="link-icon"><AppIcon name="library" :size="20" /></div>
        <div class="link-info">
          <strong>题库管理</strong>
          <p>对全站题目进行增删改查及导入</p>
        </div>
        <AppIcon name="chevron-right" :size="16" class="link-arrow" />
      </RouterLink>

      <RouterLink to="/admin/users" class="link-card">
        <div class="link-icon"><AppIcon name="user" :size="20" /></div>
        <div class="link-info">
          <strong>用户管理</strong>
          <p>列表、详情、创建、更新和删除</p>
        </div>
        <AppIcon name="chevron-right" :size="16" class="link-arrow" />
      </RouterLink>

      <RouterLink to="/admin/ai-configs" class="link-card">
        <div class="link-icon accent"><AppIcon name="spark" :size="20" /></div>
        <div class="link-info">
          <strong>系统 AI 配置</strong>
          <p>系统级模型、默认配置和策略维护</p>
        </div>
        <AppIcon name="chevron-right" :size="16" class="link-arrow" />
      </RouterLink>

      <RouterLink to="/admin/email" class="link-card">
        <div class="link-icon"><AppIcon name="info" :size="20" /></div>
        <div class="link-info">
          <strong>邮件配置</strong>
          <p>SMTP、模板和通知链路配置</p>
        </div>
        <AppIcon name="chevron-right" :size="16" class="link-arrow" />
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 4px;
}

.page-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--bg-soft);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.accent {
  background: var(--accent-soft);
  color: var(--accent);
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 11px;
  color: var(--support);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}

.stat-info strong {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}

/* Links */
.link-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.link-card:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-md);
}

.link-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--bg-soft);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.link-icon.accent {
  background: var(--accent-soft);
  color: var(--accent);
}

.link-info {
  flex: 1;
  min-width: 0;
}

.link-info strong {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 2px;
}

.link-info p {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
}

.link-arrow {
  color: var(--support);
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.link-card:hover .link-arrow {
  transform: translateX(4px);
  color: var(--accent);
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
