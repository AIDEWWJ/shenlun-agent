<script setup lang="ts">
defineProps<{
  username: string
  email: string
  saving: boolean
}>()

const emit = defineEmits<{
  'update:username': [value: string]
  'update:email': [value: string]
  submit: []
}>()

function updateUsername(event: Event) {
  emit('update:username', (event.target as HTMLInputElement).value)
}

function updateEmail(event: Event) {
  emit('update:email', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <section class="sub-card">
    <h3>个人资料</h3>
    <div class="field">
      <label for="profile-username">用户名</label>
      <input id="profile-username" :value="username" placeholder="填写新的用户名" @input="updateUsername" />
    </div>
    <div class="field">
      <label for="profile-email">邮箱</label>
      <input id="profile-email" :value="email" placeholder="填写新的邮箱" type="email" @input="updateEmail" />
    </div>
    <button class="primary-button" :disabled="saving" type="button" @click="$emit('submit')">
      {{ saving ? '保存中...' : '保存个人资料' }}
    </button>
  </section>
</template>
