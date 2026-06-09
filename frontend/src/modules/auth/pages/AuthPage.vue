<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import {
  resetForgottenPassword,
  sendForgotPasswordVerificationCode,
} from '../services/auth.service'
import {
  authStore,
  loginWithPassword,
  registerAndLogin,
  requestRegisterCode,
  setPersistSession,
} from '../store'

const route = useRoute()
const router = useRouter()

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', email: '', verificationCode: '', password: '' })
const forgotForm = reactive({ username: '', email: '', verificationCode: '', newPassword: '' })

const feedbackMessage = ref('')
const feedbackTone = ref<'error' | 'success'>('success')
const registerCodeBusy = ref(false)
const forgotCodeBusy = ref(false)
const forgotBusy = ref(false)
const registerStep = ref<1 | 2>(1)
const forgotStep = ref<1 | 2>(1)
const rememberSession = ref(authStore.persistSession)
const panelMode = ref<'login' | 'register' | 'reset'>('login')

const activeNotice = computed(() => feedbackMessage.value || authStore.error || authStore.notice)
const activeNoticeTone = computed<'error' | 'success'>(() => (
  feedbackTone.value === 'error' || Boolean(authStore.error) ? 'error' : 'success'
))
const redirectTo = computed(() => String(route.query.redirect || '/papers'))

const formTitle = computed(() => {
  if (panelMode.value === 'register') return '创建账号'
  if (panelMode.value === 'reset') return '重置密码'
  return '登录'
})

const formDesc = computed(() => {
  if (panelMode.value === 'register') return '注册后可保存练习记录与 AI 批改报告'
  if (panelMode.value === 'reset') return '通过邮箱验证码重置密码'
  return '登录后继续你的练习'
})

watch(
  () => authStore.user,
  (user) => { if (user) void router.replace(redirectTo.value) },
  { immediate: true },
)

function resetFeedback() { feedbackMessage.value = '' }
function pushFeedback(message: string, tone: 'error' | 'success') {
  feedbackMessage.value = message
  feedbackTone.value = tone
}
function switchMode(mode: 'login' | 'register' | 'reset') {
  resetFeedback()
  registerStep.value = 1
  forgotStep.value = 1
  panelMode.value = mode
}
function handleRememberSessionChange() { setPersistSession(rememberSession.value) }

async function handleLogin() {
  resetFeedback()
  try { await loginWithPassword({ username: loginForm.username.trim(), password: loginForm.password }) } catch {}
}

async function handleSendRegisterCode() {
  if (registerCodeBusy.value) return
  if (registerForm.username.trim().length < 3) { pushFeedback('用户名至少需要 3 个字符。', 'error'); return }
  if (!registerForm.email.trim()) { pushFeedback('请输入正确的邮箱地址。', 'error'); return }
  resetFeedback()
  registerCodeBusy.value = true
  try {
    await requestRegisterCode({ username: registerForm.username.trim(), email: registerForm.email.trim() })
    registerStep.value = 2
    pushFeedback(`验证码已发送至 ${registerForm.email.trim()}`, 'success')
  } catch {} finally { registerCodeBusy.value = false }
}

async function handleRegister() {
  resetFeedback()
  try {
    await registerAndLogin({
      username: registerForm.username.trim(),
      email: registerForm.email.trim(),
      password: registerForm.password,
      verification_code: registerForm.verificationCode.trim(),
    })
  } catch {}
}

async function handleSendForgotCode() {
  if (forgotCodeBusy.value) return
  if (!forgotForm.username.trim()) { pushFeedback('请输入用户名。', 'error'); return }
  if (!forgotForm.email.trim()) { pushFeedback('请输入邮箱地址。', 'error'); return }
  resetFeedback()
  forgotCodeBusy.value = true
  try {
    await sendForgotPasswordVerificationCode({ username: forgotForm.username.trim(), email: forgotForm.email.trim() })
    forgotStep.value = 2
    pushFeedback(`验证码已发送至 ${forgotForm.email.trim()}`, 'success')
  } catch (error) {
    pushFeedback(error instanceof Error ? error.message : '发送验证码失败', 'error')
  } finally { forgotCodeBusy.value = false }
}

async function handleResetPassword() {
  if (forgotBusy.value) return
  resetFeedback()
  forgotBusy.value = true
  try {
    await resetForgottenPassword({
      username: forgotForm.username.trim(),
      email: forgotForm.email.trim(),
      new_password: forgotForm.newPassword,
      verification_code: forgotForm.verificationCode.trim(),
    })
    pushFeedback('密码已成功重置', 'success')
    switchMode('login')
  } catch (error) {
    pushFeedback(error instanceof Error ? error.message : '重置失败', 'error')
  } finally { forgotBusy.value = false }
}
</script>

<template>
  <div class="auth-page">
    <!-- Left Branding -->
    <aside class="auth-brand-panel">
      <div class="brand-content">
        <RouterLink to="/" class="brand-logo">
          <span class="brand-mark">申</span>
          <span class="brand-text">申论练习平台</span>
        </RouterLink>
        <div class="brand-copy">
          <h2>系统化训练<br/>每一步都有方向</h2>
          <p>精选真题、沉浸书写、AI 深度批改，让每次练习都指向真实的进步。</p>
        </div>
        <span class="brand-footer">&copy; 2024 Shenlun Agent</span>
      </div>
    </aside>

    <!-- Right Form -->
    <main class="auth-form-panel">
      <div class="form-container">
        <header class="form-header">
          <RouterLink to="/" class="back-link">← 返回首页</RouterLink>
          <h1>{{ formTitle }}</h1>
          <p>{{ formDesc }}</p>
        </header>

        <div class="form-card">
          <NoticeBanner v-if="activeNotice" :message="activeNotice" :tone="activeNoticeTone" class="mb-5" />

          <!-- Tabs -->
          <div class="mode-tabs">
            <button @click="switchMode('login')" class="mode-tab" :class="{ active: panelMode === 'login' }">登录</button>
            <button @click="switchMode('register')" class="mode-tab" :class="{ active: panelMode === 'register' }">注册</button>
            <button @click="switchMode('reset')" class="mode-tab" :class="{ active: panelMode === 'reset' }">找回</button>
          </div>

          <!-- Login -->
          <transition name="fade" mode="out-in">
            <form v-if="panelMode === 'login'" key="login" class="form-fields" @submit.prevent="handleLogin">
              <div class="field">
                <label for="login-username">用户名</label>
                <input id="login-username" v-model.trim="loginForm.username" autocomplete="username" placeholder="请输入用户名" />
              </div>
              <div class="field">
                <label for="login-password">密码</label>
                <input id="login-password" v-model="loginForm.password" autocomplete="current-password" type="password" placeholder="请输入密码" />
              </div>
              <div class="form-row">
                <label class="checkbox-label">
                  <input v-model="rememberSession" type="checkbox" @change="handleRememberSessionChange" />
                  <span>记住登录</span>
                </label>
                <button type="button" @click="switchMode('reset')" class="link-btn">忘记密码?</button>
              </div>
              <button class="submit-btn" :disabled="authStore.busy" type="submit">
                {{ authStore.busy ? '认证中...' : '登录' }}
              </button>
            </form>

            <!-- Register -->
            <form v-else-if="panelMode === 'register'" key="register" class="form-fields" @submit.prevent="handleRegister">
              <template v-if="registerStep === 1">
                <div class="field">
                  <label for="reg-username">用户名</label>
                  <input id="reg-username" v-model.trim="registerForm.username" autocomplete="username" placeholder="至少 3 个字符" />
                </div>
                <div class="field">
                  <label for="reg-email">邮箱</label>
                  <input id="reg-email" v-model.trim="registerForm.email" autocomplete="email" type="email" placeholder="用于接收验证码" />
                </div>
                <button class="submit-btn" :disabled="registerCodeBusy" type="button" @click="handleSendRegisterCode">
                  {{ registerCodeBusy ? '发送中...' : '发送验证码' }}
                </button>
              </template>
              <template v-else>
                <div class="field">
                  <label for="reg-code">验证码</label>
                  <input id="reg-code" v-model.trim="registerForm.verificationCode" autocomplete="one-time-code" placeholder="邮箱验证码" />
                </div>
                <div class="field">
                  <label for="reg-password">设置密码</label>
                  <input id="reg-password" v-model="registerForm.password" autocomplete="new-password" type="password" placeholder="至少 6 位" />
                </div>
                <div class="btn-group">
                  <button class="secondary-btn" type="button" @click="registerStep = 1">上一步</button>
                  <button class="submit-btn" :disabled="authStore.busy" type="submit">
                    {{ authStore.busy ? '创建中...' : '完成注册' }}
                  </button>
                </div>
              </template>
            </form>

            <!-- Reset -->
            <form v-else key="reset" class="form-fields" @submit.prevent="handleResetPassword">
              <template v-if="forgotStep === 1">
                <div class="field">
                  <label for="forgot-username">用户名</label>
                  <input id="forgot-username" v-model.trim="forgotForm.username" placeholder="请输入用户名" />
                </div>
                <div class="field">
                  <label for="forgot-email">邮箱</label>
                  <input id="forgot-email" v-model.trim="forgotForm.email" type="email" placeholder="注册邮箱" />
                </div>
                <button class="submit-btn" :disabled="forgotCodeBusy" type="button" @click="handleSendForgotCode">
                  {{ forgotCodeBusy ? '发送中...' : '发送验证码' }}
                </button>
              </template>
              <template v-else>
                <div class="field">
                  <label for="forgot-code">验证码</label>
                  <input id="forgot-code" v-model.trim="forgotForm.verificationCode" placeholder="邮箱验证码" />
                </div>
                <div class="field">
                  <label for="forgot-password">新密码</label>
                  <input id="forgot-password" v-model="forgotForm.newPassword" type="password" placeholder="请输入新密码" />
                </div>
                <div class="btn-group">
                  <button class="secondary-btn" type="button" @click="forgotStep = 1">上一步</button>
                  <button class="submit-btn" :disabled="forgotBusy" type="submit">
                    {{ forgotBusy ? '提交中...' : '确认重置' }}
                  </button>
                </div>
              </template>
            </form>
          </transition>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
}

/* Brand Panel */
.auth-brand-panel {
  display: none;
  width: 44%;
  background: var(--accent-deep);
  position: relative;
  overflow: hidden;
}

@media (min-width: 1024px) {
  .auth-brand-panel { display: flex; }
}

.brand-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 40px;
  width: 100%;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif);
  font-weight: 700;
  font-size: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-text {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.brand-copy {
  max-width: 340px;
}

.brand-copy h2 {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  line-height: 1.35;
  margin-bottom: 14px;
}

.brand-copy p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.7;
}

.brand-footer {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
}

/* Form Panel */
.auth-form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  background: var(--bg);
}

.form-container {
  width: 100%;
  max-width: 380px;
}

.form-header {
  margin-bottom: 24px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  margin-bottom: 16px;
  padding: 4px 0;
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: var(--accent);
}

.form-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-sans);
  margin-bottom: 6px;
}

.form-header p {
  font-size: 13px;
  color: var(--muted);
}

.form-card {
  background: var(--paper);
  padding: 24px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}

/* Mode Tabs */
.mode-tabs {
  display: flex;
  gap: 2px;
  padding: 3px;
  background: var(--bg-soft);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
}

.mode-tab {
  flex: 1;
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  background: transparent;
  border: none;
  transition: all var(--transition-fast);
}

.mode-tab.active {
  background: var(--paper);
  color: var(--accent);
  box-shadow: var(--shadow-soft);
}

.mode-tab:not(.active):hover {
  color: var(--ink);
}

/* Form Fields */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--bg-soft);
  color: var(--ink);
  font-size: 14px;
  outline: none;
  transition: all var(--transition-fast);
}

.field input:focus {
  border-color: var(--accent);
  background: var(--paper);
  box-shadow: var(--ring);
}

.field input::placeholder {
  color: var(--support);
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--accent);
}

.link-btn {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  background: none;
  border: none;
  padding: 0;
}

.link-btn:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  padding: 11px;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  border: none;
  transition: all var(--transition-fast);
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-deep);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.secondary-btn {
  flex: 1;
  padding: 11px;
  border-radius: var(--radius-md);
  background: var(--bg-soft);
  color: var(--ink);
  font-size: 14px;
  font-weight: 600;
  border: 1px solid var(--line);
  transition: all var(--transition-fast);
}

.secondary-btn:hover:not(:disabled) {
  background: var(--bg-strong);
}

.btn-group {
  display: flex;
  gap: 8px;
}

.btn-group .submit-btn {
  flex: 1;
}

/* Transition */
.fade-enter-active {
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-leave-active {
  transition: opacity 0.12s cubic-bezier(0.4, 0, 1, 1),
              transform 0.12s cubic-bezier(0.4, 0, 1, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(6px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}
</style>
