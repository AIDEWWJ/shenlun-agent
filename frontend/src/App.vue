<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { API_BASE_URL, ApiError, request } from './services/api'
import { authStore, bootstrapAuth, loginWithPassword, logout, registerAndLogin, setAuthMode } from './stores/auth'

type PracticeAction = {
  endpoint: '/analyze' | '/outline' | '/review'
  label: string
  description: string
}

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

const feedbackMessage = ref('')
const feedbackTone = ref<'error' | 'success'>('success')
const actionBusy = ref(false)
const actionResult = ref('登录后点击右侧按钮，就可以验证受保护接口是否真的带上了 Bearer Token。')

const practiceActions: PracticeAction[] = [
  {
    endpoint: '/analyze',
    label: '验证题目分析',
    description: '调用 `/api/analyze`，确认未登录时会被拦截，登录后可访问。',
  },
  {
    endpoint: '/outline',
    label: '验证提纲生成',
    description: '调用 `/api/outline`，检查 token 是否被自动附带。',
  },
  {
    endpoint: '/review',
    label: '验证批改接口',
    description: '调用 `/api/review`，验证当前用户身份是否能被后端识别。',
  },
]

const tokenPreview = computed(() => {
  if (!authStore.token) {
    return '未登录'
  }

  if (authStore.token.length <= 36) {
    return authStore.token
  }

  return `${authStore.token.slice(0, 20)}...${authStore.token.slice(-12)}`
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
  setAuthMode(mode)
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString('zh-CN', {
    hour12: false,
  })
}

async function handleLogin() {
  resetFeedback()

  try {
    await loginWithPassword({
      username: loginForm.username.trim(),
      password: loginForm.password,
    })
    loginForm.password = ''
    actionResult.value = '登录成功，现在你可以点击下方任一按钮验证受保护接口。'
  } catch {
    // Store has already recorded a user-facing error message.
  }
}

async function handleRegister() {
  resetFeedback()

  if (registerForm.password !== registerForm.confirmPassword) {
    pushFeedback('两次输入的密码不一致，请重新确认。', 'error')
    return
  }

  try {
    await registerAndLogin({
      username: registerForm.username.trim(),
      email: registerForm.email.trim() || null,
      password: registerForm.password,
    })

    registerForm.password = ''
    registerForm.confirmPassword = ''
    actionResult.value = '注册并自动登录成功。下面可以直接验证鉴权接口。'
  } catch {
    // Store has already recorded a user-facing error message.
  }
}

function handleLogout() {
  logout()
  actionResult.value = '已退出登录。此时再请求受保护接口会返回 401。'
}

async function runProtectedAction(action: PracticeAction) {
  if (!authStore.token) {
    pushFeedback('请先登录后再请求受保护接口。', 'error')
    return
  }

  resetFeedback()
  actionBusy.value = true
  actionResult.value = `正在请求 ${action.endpoint} ...`

  try {
    const response = await request<Record<string, unknown>>(action.endpoint, {
      method: 'POST',
      token: authStore.token,
    })
    actionResult.value = JSON.stringify(response, null, 2)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      handleLogout()
      pushFeedback('登录状态已失效，请重新登录。', 'error')
    } else if (error instanceof Error) {
      actionResult.value = error.message
    } else {
      actionResult.value = '请求失败，请稍后重试。'
    }
  } finally {
    actionBusy.value = false
  }
}

onMounted(() => {
  void bootstrapAuth()
})
</script>

<template>
  <main class="app-shell">
    <section class="page-grid">
      <aside class="brand-panel">
        <p class="eyebrow">Shenlun Agent</p>
        <h1>登录后进入你的申论训练工作台</h1>
        <p class="lead">
          这版前端已经接上注册、登录、JWT 持久化和受保护接口验证。你可以直接用它确认整套鉴权流程是否跑通。
        </p>

        <div class="feature-list">
          <article class="feature-card">
            <h2>注册即用</h2>
            <p>新用户注册后会自动登录，不需要再额外手动请求 token。</p>
          </article>
          <article class="feature-card">
            <h2>状态恢复</h2>
            <p>浏览器刷新后会尝试恢复本地 token，并重新拉取当前用户信息。</p>
          </article>
          <article class="feature-card">
            <h2>鉴权验证</h2>
            <p>右侧三个练习接口都需要 Bearer Token，最适合先做联调验证。</p>
          </article>
        </div>

        <div class="meta-card">
          <span class="meta-label">API Base URL</span>
          <code>{{ API_BASE_URL }}</code>
        </div>
      </aside>

      <section class="console-panel">
        <div v-if="!authStore.initialized" class="panel loading-panel">
          <p class="panel-kicker">会话恢复中</p>
          <h2>正在检查本地登录状态</h2>
          <p>如果你之前已经登录，这里会自动恢复当前会话。</p>
        </div>

        <template v-else-if="!authStore.user">
          <div class="panel auth-panel">
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

            <form v-if="authStore.mode === 'login'" class="form-grid" @submit.prevent="handleLogin">
              <div class="field">
                <label for="login-username">用户名</label>
                <input id="login-username" v-model.trim="loginForm.username" autocomplete="username" placeholder="请输入用户名" required />
              </div>
              <div class="field">
                <label for="login-password">密码</label>
                <input id="login-password" v-model="loginForm.password" autocomplete="current-password" placeholder="请输入密码" required type="password" />
              </div>
              <button class="primary-button" :disabled="authStore.busy" type="submit">
                {{ authStore.busy ? '登录中...' : '立即登录' }}
              </button>
            </form>

            <form v-else class="form-grid" @submit.prevent="handleRegister">
              <div class="field">
                <label for="register-username">用户名</label>
                <input id="register-username" v-model.trim="registerForm.username" autocomplete="username" placeholder="至少 3 个字符" required />
              </div>
              <div class="field">
                <label for="register-email">邮箱</label>
                <input id="register-email" v-model.trim="registerForm.email" autocomplete="email" placeholder="可选，用于找回或通知" type="email" />
              </div>
              <div class="field">
                <label for="register-password">密码</label>
                <input id="register-password" v-model="registerForm.password" autocomplete="new-password" placeholder="至少 6 位" required type="password" />
              </div>
              <div class="field">
                <label for="register-confirm">确认密码</label>
                <input id="register-confirm" v-model="registerForm.confirmPassword" autocomplete="new-password" placeholder="再次输入密码" required type="password" />
              </div>
              <button class="primary-button" :disabled="authStore.busy" type="submit">
                {{ authStore.busy ? '注册中...' : '创建账号并登录' }}
              </button>
            </form>

            <p
              v-if="feedbackMessage || authStore.error || authStore.notice"
              class="feedback"
              :class="{
                'is-error': feedbackTone === 'error' || Boolean(authStore.error),
                'is-success': !feedbackMessage && !authStore.error && Boolean(authStore.notice),
              }"
            >
              {{ feedbackMessage || authStore.error || authStore.notice }}
            </p>
          </div>
        </template>

        <template v-else>
          <div class="panel session-panel">
            <div class="session-header">
              <div>
                <p class="panel-kicker">当前会话</p>
                <h2>{{ authStore.user.username }}</h2>
              </div>
              <button class="ghost-button" type="button" @click="handleLogout">退出登录</button>
            </div>

            <div class="identity-grid">
              <div class="identity-item">
                <span>邮箱</span>
                <strong>{{ authStore.user.email || '未填写' }}</strong>
              </div>
              <div class="identity-item">
                <span>状态</span>
                <strong>{{ authStore.user.status }}</strong>
              </div>
              <div class="identity-item">
                <span>创建时间</span>
                <strong>{{ formatDate(authStore.user.created_at) }}</strong>
              </div>
              <div class="identity-item">
                <span>Token 预览</span>
                <strong class="token-preview">{{ tokenPreview }}</strong>
              </div>
            </div>

            <div class="role-row">
              <span class="role-badge" v-for="role in authStore.user.roles" :key="role">
                {{ role }}
              </span>
            </div>
          </div>

          <div class="panel workspace-panel">
            <div class="workspace-header">
              <div>
                <p class="panel-kicker">鉴权验证台</p>
                <h2>调用需要登录的接口</h2>
              </div>
              <span class="workspace-hint">Bearer Token 已自动从本地登录态读取</span>
            </div>

            <div class="action-list">
              <button
                v-for="action in practiceActions"
                :key="action.endpoint"
                class="action-card"
                :disabled="actionBusy"
                type="button"
                @click="runProtectedAction(action)"
              >
                <strong>{{ action.label }}</strong>
                <span>{{ action.description }}</span>
              </button>
            </div>

            <pre class="response-box">{{ actionResult }}</pre>
          </div>
        </template>
      </section>
    </section>
  </main>
</template>
