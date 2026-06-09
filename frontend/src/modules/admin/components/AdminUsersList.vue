<script setup lang="ts">
import type { UserRead } from '@/modules/auth/types/auth'

defineProps<{
  users: UserRead[]
  loading: boolean
  deletingUserId: number | null
}>()

defineEmits<{
  edit: [user: UserRead]
  delete: [userId: number]
}>()
</script>

<template>
  <div>
    <span v-if="loading" class="workspace-hint">加载中...</span>
    <div v-if="users.length === 0" class="empty-state">当前没有用户数据。</div>
    <div v-else class="user-table">
      <div class="user-table-head user-table-row">
        <span>ID</span>
        <span>用户名</span>
        <span>邮箱</span>
        <span>状态</span>
        <span>角色</span>
        <span>操作</span>
      </div>
      <div v-for="user in users" :key="user.id" class="user-table-row">
        <span>#{{ user.id }}</span>
        <span>{{ user.username }}</span>
        <span>{{ user.email || '未填写' }}</span>
        <span>{{ user.status }}</span>
        <span>{{ user.roles.join('、') }}</span>
        <span class="action-row">
          <button class="ghost-button" type="button" @click="$emit('edit', user)">编辑</button>
          <button class="ghost-button" :disabled="deletingUserId === user.id" type="button" @click="$emit('delete', user.id)">
            {{ deletingUserId === user.id ? '删除中...' : '删除' }}
          </button>
        </span>
      </div>
    </div>
  </div>
</template>
