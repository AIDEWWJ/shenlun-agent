<script setup lang="ts">
defineProps<{
  currentPassword: string
  newPassword: string
  saving: boolean
}>()

const emit = defineEmits<{
  'update:currentPassword': [value: string]
  'update:newPassword': [value: string]
  submit: []
}>()

function updateCurrentPassword(event: Event) {
  emit('update:currentPassword', (event.target as HTMLInputElement).value)
}

function updateNewPassword(event: Event) {
  emit('update:newPassword', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <section class="sub-card">
    <h3>修改密码</h3>
    <div class="field">
      <label for="password-current">当前密码</label>
      <input id="password-current" :value="currentPassword" autocomplete="current-password" type="password" @input="updateCurrentPassword" />
    </div>
    <div class="field">
      <label for="password-new">新密码</label>
      <input id="password-new" :value="newPassword" autocomplete="new-password" type="password" @input="updateNewPassword" />
    </div>
    <button class="primary-button" :disabled="saving" type="button" @click="$emit('submit')">
      {{ saving ? '提交中...' : '修改密码' }}
    </button>
  </section>
</template>
