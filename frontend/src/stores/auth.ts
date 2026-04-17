import { reactive, readonly } from 'vue'

import { fetchCurrentUser, loginUser, registerUser, type LoginPayload, type RegisterPayload, type UserRead } from '../services/auth'

type AuthMode = 'login' | 'register'

type AuthState = {
  initialized: boolean
  busy: boolean
  token: string | null
  user: UserRead | null
  error: string
  notice: string
  mode: AuthMode
}

const AUTH_STORAGE_KEY = 'shenlun-agent-access-token'

function loadStoredToken(): string | null {
  try {
    return localStorage.getItem(AUTH_STORAGE_KEY)
  } catch {
    return null
  }
}

function saveStoredToken(token: string) {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, token)
  } catch {
    // Ignore storage write errors in private browsing or restricted environments.
  }
}

function clearStoredToken() {
  try {
    localStorage.removeItem(AUTH_STORAGE_KEY)
  } catch {
    // Ignore storage cleanup errors.
  }
}

function resolveMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

const state = reactive<AuthState>({
  initialized: false,
  busy: false,
  token: loadStoredToken(),
  user: null,
  error: '',
  notice: '',
  mode: 'login',
})

function clearSession() {
  state.token = null
  state.user = null
  clearStoredToken()
}

export const authStore = readonly(state)

export function setAuthMode(mode: AuthMode) {
  state.mode = mode
  state.error = ''
  state.notice = ''
}

export async function bootstrapAuth() {
  if (state.initialized) {
    return
  }

  if (!state.token) {
    state.initialized = true
    return
  }

  try {
    state.user = await fetchCurrentUser(state.token)
  } catch (error) {
    clearSession()
    state.error = resolveMessage(error, '登录状态已失效，请重新登录')
  } finally {
    state.initialized = true
  }
}

export async function loginWithPassword(payload: LoginPayload) {
  state.busy = true
  state.error = ''
  state.notice = ''

  try {
    const token = await loginUser(payload)
    state.token = token.access_token
    saveStoredToken(token.access_token)
    state.user = await fetchCurrentUser(token.access_token)
    state.notice = '登录成功'
  } catch (error) {
    clearSession()
    state.error = resolveMessage(error, '登录失败，请稍后重试')
    throw error
  } finally {
    state.busy = false
    state.initialized = true
  }
}

export async function registerAndLogin(payload: RegisterPayload) {
  state.busy = true
  state.error = ''
  state.notice = ''

  try {
    await registerUser(payload)
    state.notice = '注册成功，正在为你自动登录'
    const token = await loginUser({
      username: payload.username,
      password: payload.password,
    })
    state.token = token.access_token
    saveStoredToken(token.access_token)
    state.user = await fetchCurrentUser(token.access_token)
    state.notice = '注册成功，已自动登录'
  } catch (error) {
    clearSession()
    state.error = resolveMessage(error, '注册失败，请稍后重试')
    throw error
  } finally {
    state.busy = false
    state.initialized = true
  }
}

export function logout() {
  clearSession()
  state.error = ''
  state.notice = '已退出登录'
}
