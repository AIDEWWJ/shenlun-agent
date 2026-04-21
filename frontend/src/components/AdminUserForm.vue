<script setup lang="ts">
defineProps<{
  title: string
  username: string
  password: string
  email: string
  status: string
  rolesText: string
  saving: boolean
  submitLabel: string
  resetLabel: string
}>()

const emit = defineEmits<{
  'update:username': [value: string]
  'update:password': [value: string]
  'update:email': [value: string]
  'update:status': [value: string]
  'update:rolesText': [value: string]
  submit: []
  reset: []
}>()

function updateUsername(event: Event) {
  emit('update:username', (event.target as HTMLInputElement).value)
}

function updatePassword(event: Event) {
  emit('update:password', (event.target as HTMLInputElement).value)
}

function updateEmail(event: Event) {
  emit('update:email', (event.target as HTMLInputElement).value)
}

function updateStatus(event: Event) {
  emit('update:status', (event.target as HTMLInputElement).value)
}

function updateRolesText(event: Event) {
  emit('update:rolesText', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <section class="sub-card admin-form-card">
    <div class="section-header compact">
      <h3>{{ title }}</h3>
      <button class="ghost-button" type="button" @click="$emit('reset')">{{ resetLabel }}</button>
    </div>

    <div class="form-grid admin-form-grid">
      <div class="field">
        <label>用户名</label>
        <input :value="username" placeholder="用户名" @input="updateUsername" />
      </div>
      <div class="field">
        <label>密码</label>
        <input :value="password" :placeholder="title.includes('编辑') ? '留空表示不修改' : '初始密码'" type="password" @input="updatePassword" />
      </div>
      <div class="field">
        <label>邮箱</label>
        <input :value="email" placeholder="邮箱" type="email" @input="updateEmail" />
      </div>
      <div class="field">
        <label>状态</label>
        <input :value="status" placeholder="active / inactive" @input="updateStatus" />
      </div>
      <div class="field field-wide">
        <label>角色（英文逗号分隔）</label>
        <input :value="rolesText" placeholder="learner, admin" @input="updateRolesText" />
      </div>
    </div>

    <p class="form-hint">常用角色：visitor、learner、admin</p>
    <button class="primary-button" :disabled="saving" type="button" @click="$emit('submit')">
      {{ saving ? '保存中...' : submitLabel }}
    </button>
  </section>
</template>
