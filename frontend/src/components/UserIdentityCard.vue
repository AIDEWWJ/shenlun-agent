<script setup lang="ts">
import { type UserRead } from '../services/auth'

defineProps<{
  user: Omit<UserRead, 'roles'> & { roles: readonly string[] }
  tokenPreview: string
}>()
</script>

<template>
  <div class="panel session-panel compact-panel">
    <div class="session-header">
      <div>
        <p class="panel-kicker">当前状态</p>
        <h2>{{ user.username }}</h2>
      </div>
    </div>

    <div class="identity-grid">
      <div class="identity-item">
        <span>邮箱</span>
        <strong>{{ user.email || '未填写' }}</strong>
      </div>
      <div class="identity-item">
        <span>状态</span>
        <strong>{{ user.status }}</strong>
      </div>
      <div class="identity-item">
        <span>创建时间</span>
        <strong>{{ new Date(user.created_at).toLocaleString('zh-CN', { hour12: false }) }}</strong>
      </div>
      <div class="identity-item">
        <span>登录状态</span>
        <strong class="token-preview">{{ tokenPreview }}</strong>
      </div>
    </div>

    <div class="role-row">
      <span class="role-badge" v-for="role in user.roles" :key="role">{{ role }}</span>
    </div>
  </div>
</template>
