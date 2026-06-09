<script setup lang="ts">
import { reactive, ref } from 'vue'

import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { changeCurrentUserPassword } from '@/modules/auth/services/auth.service'
import { authStore } from '@/modules/auth/store'
import PasswordChangeForm from '../components/PasswordChangeForm.vue'

const passwordForm = reactive({ currentPassword: '', newPassword: '' })
const changing = ref(false)
const notice = ref('')
const error = ref('')

async function savePassword() {
  if (!authStore.token) return
  changing.value = true; notice.value = ''; error.value = ''
  try {
    await changeCurrentUserPassword(authStore.token, { current_password: passwordForm.currentPassword, new_password: passwordForm.newPassword })
    passwordForm.currentPassword = ''; passwordForm.newPassword = ''
    notice.value = '密码修改成功'
  } catch (err) { error.value = err instanceof Error ? err.message : '修改密码失败' }
  finally { changing.value = false }
}
</script>

<template>
  <div class="page-content">
    <header class="section-header">
      <h1>安全设置</h1>
      <p>修改登录密码</p>
    </header>

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <div class="card">
      <div class="card-header">
        <h3>修改密码</h3>
        <p>为了账号安全，建议每 3 个月更新一次密码</p>
      </div>
      <div class="card-body">
        <PasswordChangeForm
          :current-password="passwordForm.currentPassword"
          :new-password="passwordForm.newPassword"
          :saving="changing"
          @update:currentPassword="passwordForm.currentPassword = $event"
          @update:newPassword="passwordForm.newPassword = $event"
          @submit="savePassword"
        />
      </div>
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
  gap: 20px;
}

.section-header {
  display: flex;
  flex-direction: column;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}

.section-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 4px;
}

.section-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
}

.card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.card-header {
  padding: 20px 28px 16px;
  border-bottom: 1px solid var(--line-soft);
}

.card-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 4px;
}

.card-header p {
  font-size: 12px;
  color: var(--muted);
}

.card-body {
  padding: 24px 28px 28px;
}
</style>
