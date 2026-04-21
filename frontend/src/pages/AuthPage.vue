<script setup lang="ts">
import { computed, defineAsyncComponent, reactive, ref } from 'vue'

import {
  resetForgottenPassword,
  sendForgotPasswordVerificationCode,
} from '../services/auth'
import {
  authStore,
  loginWithPassword,
  registerAndLogin,
  requestRegisterCode,
  setAuthMode,
  setPersistSession,
} from '../stores/auth'

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  verificationCode: '',
  password: '',
})

const forgotForm = reactive({
  username: '',
  email: '',
  verificationCode: '',
  newPassword: '',
})

const feedbackMessage = ref('')
const feedbackTone = ref<'error' | 'success'>('success')
const showLoginPassword = ref(false)
const showRegisterPassword = ref(false)
const showForgotPassword = ref(false)
const forgotBusy = ref(false)
const registerCodeBusy = ref(false)
const forgotCodeBusy = ref(false)
const registerStep = ref<1 | 2>(1)
const forgotStep = ref<1 | 2>(1)
const rememberSession = ref(authStore.persistSession)
const NoticeBanner = defineAsyncComponent(() => import('../components/NoticeBanner.vue'))

const activeNotice = computed(() => feedbackMessage.value || authStore.error || authStore.notice)
const activeNoticeTone = computed<'error' | 'success'>(() => (feedbackTone.value === 'error' || Boolean(authStore.error) ? 'error' : 'success'))

const authContext = computed(() =>
  showForgotPassword.value ? '' : '登录或注册后继续你的申论练习。',
)

const registerCodeSentHint = computed(() =>
  registerForm.email.trim() ? `验证码已发送至 ${registerForm.email.trim()}` : '验证码已发送，请查收邮箱。',
)

const forgotCodeSentHint = computed(() =>
  forgotForm.email.trim() ? `验证码已发送至 ${forgotForm.email.trim()}` : '验证码已发送，请查收邮箱。',
)

const formHint = computed(() => {
  if (showForgotPassword.value) {
    return forgotStep.value === 1 ? '验证码会发送到绑定邮箱。' : '重置后使用新密码登录。'
  }

  if (authStore.mode === 'register') {
    return registerStep.value === 1 ? '验证码会发送到邮箱。' : '注册后将自动进入平台。'
  }

  return '完成后继续你的练习进度。'
})

function resetFeedback() {
  feedbackMessage.value = ''
}

function pushFeedback(message: string, tone: 'error' | 'success') {
  feedbackMessage.value = message
  feedbackTone.value = tone
}

function switchMode(mode: 'login' | 'register') {
  resetFeedback()
  showForgotPassword.value = false
  registerStep.value = 1
  registerForm.verificationCode = ''
  forgotForm.verificationCode = ''
  setAuthMode(mode)
}

function handleRememberSessionChange() {
  setPersistSession(rememberSession.value)
}

function toggleLoginPassword() {
  showLoginPassword.value = !showLoginPassword.value
}

function toggleRegisterPassword() {
  showRegisterPassword.value = !showRegisterPassword.value
}

function handleForgotPassword() {
  resetFeedback()
  showForgotPassword.value = !showForgotPassword.value
  if (showForgotPassword.value) {
    forgotStep.value = 1
    forgotForm.verificationCode = ''
  }
}

function closeForgotPassword() {
  showForgotPassword.value = false
  resetFeedback()
  forgotStep.value = 1
}

function goToRegisterStepTwo() {
  resetFeedback()

  if (registerForm.username.trim().length < 3) {
    pushFeedback('用户名至少 3 个字符。', 'error')
    return
  }

  if (registerForm.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email.trim())) {
    pushFeedback('请输入有效的邮箱地址。', 'error')
    return
  }

  void sendRegisterCode()
}

function backToRegisterStepOne() {
  resetFeedback()
  registerStep.value = 1
  registerForm.verificationCode = ''
}

async function sendRegisterCode() {
  if (registerCodeBusy.value) {
    return
  }

  registerCodeBusy.value = true
  resetFeedback()

  try {
    await requestRegisterCode({
      username: registerForm.username.trim(),
      email: registerForm.email.trim(),
    })
    registerStep.value = 2
    pushFeedback(`验证码已发送至 ${registerForm.email.trim()}，请查收邮箱。`, 'success')
  } catch {
    // Store already exposes the message.
  } finally {
    registerCodeBusy.value = false
  }
}

async function sendForgotCode() {
  if (forgotCodeBusy.value) {
    return
  }

  forgotCodeBusy.value = true
  resetFeedback()

  try {
    await sendForgotPasswordVerificationCode({
      username: forgotForm.username.trim(),
      email: forgotForm.email.trim(),
    })
    forgotStep.value = 2
    pushFeedback(`验证码已发送至 ${forgotForm.email.trim()}，请查收邮箱。`, 'success')
  } catch {
    // Store already exposes the message.
  } finally {
    forgotCodeBusy.value = false
  }
}

async function handleLogin() {
  resetFeedback()

  try {
    await loginWithPassword({
      username: loginForm.username.trim(),
      password: loginForm.password,
    })
    loginForm.password = ''
  } catch {
    // Store already exposes the message.
  }
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

    registerForm.password = ''
    registerForm.verificationCode = ''
    registerStep.value = 1
  } catch {
    // Store already exposes the message.
  }
}

async function handleForgotPasswordSubmit() {
  resetFeedback()

  if (forgotBusy.value) {
    return
  }

  try {
    forgotBusy.value = true
    await resetForgottenPassword({
      username: forgotForm.username.trim(),
      email: forgotForm.email.trim(),
      new_password: forgotForm.newPassword,
      verification_code: forgotForm.verificationCode.trim(),
    })

    forgotForm.username = ''
    forgotForm.email = ''
    forgotForm.verificationCode = ''
    forgotForm.newPassword = ''
    showForgotPassword.value = false
    pushFeedback('密码重置成功，请使用新密码重新登录。', 'success')
    setAuthMode('login')
  } catch {
    // Store already exposes the message.
  } finally {
    forgotBusy.value = false
  }
}
</script>

<template>
  <main class="app-shell auth-shell">
    <section class="page-grid auth-grid">
      <aside class="brand-panel">
        <div class="brand-sheet">
          <p class="eyebrow">Shenlun Practice Platform</p>
          <h1 class="brand-title">申论练习平台</h1>
          <p class="lead">AI 批改、错题分析、结构反馈与练习沉淀，帮助你建立更稳健的申论表达能力。</p>
        </div>

        <div class="brand-notes">
          <div class="brand-meta" aria-label="平台关键词">
            <span>思辨</span>
            <span>表达</span>
            <span>训练</span>
          </div>
          <p class="brand-caption">围绕题目理解、结构组织与表达修订，提供更贴近申论训练场景的学习入口。</p>
        </div>
      </aside>

      <section class="console-panel">
        <div v-if="!authStore.initialized" class="panel loading-panel">
          <div class="auth-body">
            <div class="auth-intro">
              <p class="panel-kicker">会话恢复中</p>
              <h2>正在检查本地登录状态</h2>
              <p class="auth-context">如果你之前已经登录，这里会自动恢复当前会话。</p>
            </div>
          </div>
        </div>

        <div v-else class="panel auth-panel">
          <div class="auth-body">
            <div class="auth-intro">
              <p class="panel-kicker">{{ showForgotPassword ? '找回入口' : '账号入口' }}</p>
              <p v-if="authContext" class="auth-context">{{ authContext }}</p>
            </div>

            <div class="auth-feedback-slot">
              <NoticeBanner v-if="activeNotice" :message="activeNotice" :tone="activeNoticeTone" />
            </div>

            <div class="tab-row">
              <button
                class="tab-button"
                :class="{ 'is-active': authStore.mode === 'login' }"
                type="button"
                @click="switchMode('login')"
              >
                登录
              </button>
              <button
                class="tab-button"
                :class="{ 'is-active': authStore.mode === 'register' }"
                type="button"
                @click="switchMode('register')"
              >
                注册
              </button>
            </div>

            <Transition name="auth-pane" mode="out-in">
              <form v-if="authStore.mode === 'login'" key="login" class="form-grid auth-form" @submit.prevent="handleLogin">
                <Transition name="auth-subpane" mode="out-in">
                  <div v-if="!showForgotPassword" key="login-fields" class="auth-form-section">
                    <div class="field">
                      <label for="login-username">用户名</label>
                      <input id="login-username" v-model.trim="loginForm.username" autocomplete="username" placeholder="请输入用户名" required />
                    </div>

                    <div class="field">
                      <label for="login-password">密码</label>
                      <div class="password-field">
                        <input
                          id="login-password"
                          v-model="loginForm.password"
                          :type="showLoginPassword ? 'text' : 'password'"
                          autocomplete="current-password"
                          placeholder="请输入密码"
                          required
                        />
                        <button
                          class="password-toggle"
                          :aria-label="showLoginPassword ? '隐藏密码' : '显示密码'"
                          type="button"
                          @click="toggleLoginPassword"
                        >
                          {{ showLoginPassword ? '隐藏' : '显示' }}
                        </button>
                      </div>
                    </div>

                    <div class="form-tools">
                      <label class="remember-row">
                        <input v-model="rememberSession" type="checkbox" @change="handleRememberSessionChange" />
                        记住登录状态
                      </label>
                      <button class="text-button" type="button" @click="handleForgotPassword">忘记密码</button>
                    </div>

                    <button class="primary-button" :disabled="authStore.busy" type="submit">
                      {{ authStore.busy ? '登录中...' : '立即登录' }}
                    </button>

                    <p class="form-hint">{{ formHint }}</p>
                  </div>

                  <div v-else key="forgot-fields" class="auth-form-section">
                    <div v-if="forgotStep === 1" class="auth-form-section">
                      <div class="field">
                        <label for="forgot-username">用户名</label>
                        <input id="forgot-username" v-model.trim="forgotForm.username" autocomplete="username" placeholder="请输入用户名" required />
                      </div>

                      <div class="field">
                        <label for="forgot-email">邮箱</label>
                        <input id="forgot-email" v-model.trim="forgotForm.email" autocomplete="email" placeholder="请输入绑定邮箱" required type="email" />
                      </div>
                    </div>

                    <div v-else class="auth-form-section">
                      <p class="status-chip is-success">{{ forgotCodeSentHint }}</p>

                      <div class="field">
                        <label for="forgot-code">验证码</label>
                        <input id="forgot-code" v-model.trim="forgotForm.verificationCode" autocomplete="one-time-code" placeholder="请输入邮箱验证码" required />
                      </div>

                      <div class="field">
                        <label for="forgot-password">新密码</label>
                        <input id="forgot-password" v-model="forgotForm.newPassword" autocomplete="new-password" placeholder="请输入新密码" required type="password" />
                      </div>
                    </div>

                    <div class="register-button-row">
                      <button class="ghost-button register-back-button" type="button" @click="closeForgotPassword">返回登录</button>
                      <button v-if="forgotStep === 1" class="primary-button" :disabled="forgotCodeBusy" type="button" @click="sendForgotCode">
                        {{ forgotCodeBusy ? '发送中...' : '发送验证码' }}
                      </button>
                      <button v-else class="primary-button" :disabled="forgotBusy" type="button" @click="handleForgotPasswordSubmit">
                        {{ forgotBusy ? '重置中...' : '重置密码' }}
                      </button>
                    </div>

                    <p class="form-hint">{{ formHint }}</p>
                  </div>
                </Transition>
              </form>

              <form v-else key="register" class="form-grid auth-form" @submit.prevent="handleRegister">
                <Transition name="auth-subpane" mode="out-in">
                  <div v-if="registerStep === 1" key="register-step-one" class="auth-form-section">
                    <div class="field">
                      <label for="register-username">用户名</label>
                      <input id="register-username" v-model.trim="registerForm.username" autocomplete="username" placeholder="至少 3 个字符" required />
                    </div>

                    <div class="field">
                      <label for="register-email">邮箱</label>
                      <input id="register-email" v-model.trim="registerForm.email" autocomplete="email" placeholder="可选，用于通知或找回" type="email" />
                    </div>

                    <div class="register-action-row">
                      <span class="register-step-note">第 1 步，共 2 步</span>
                      <button class="primary-button" :disabled="registerCodeBusy" type="button" @click="goToRegisterStepTwo">
                        {{ registerCodeBusy ? '发送中...' : '发送验证码' }}
                      </button>
                    </div>

                    <p class="form-hint">{{ formHint }}</p>
                  </div>

                <div v-else key="register-step-two" class="auth-form-section">
                    <p class="status-chip is-success">{{ registerCodeSentHint }}</p>

                    <div class="field">
                      <label for="register-code">验证码</label>
                      <input
                        id="register-code"
                        v-model.trim="registerForm.verificationCode"
                        autocomplete="one-time-code"
                        placeholder="请输入邮箱验证码"
                        required
                      />
                    </div>

                    <div class="field">
                      <label for="register-password">密码</label>
                      <div class="password-field">
                        <input
                          id="register-password"
                          v-model="registerForm.password"
                          :type="showRegisterPassword ? 'text' : 'password'"
                          autocomplete="new-password"
                          placeholder="至少 6 位密码"
                          required
                        />
                        <button
                          class="password-toggle"
                          :aria-label="showRegisterPassword ? '隐藏密码' : '显示密码'"
                          type="button"
                          @click="toggleRegisterPassword"
                        >
                          {{ showRegisterPassword ? '隐藏' : '显示' }}
                        </button>
                      </div>
                    </div>

                    <div class="register-button-row">
                      <button class="ghost-button register-back-button" type="button" @click="backToRegisterStepOne">上一步</button>
                      <button class="primary-button" :disabled="authStore.busy" type="submit">
                        {{ authStore.busy ? '注册中...' : '创建账号并登录' }}
                      </button>
                    </div>

                    <p class="form-hint">{{ formHint }}</p>
                  </div>
                </Transition>
              </form>
            </Transition>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>
