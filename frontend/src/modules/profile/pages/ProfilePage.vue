<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

import AiConfigEditor from '@/features/ai-config/components/AiConfigEditor.vue'
import AppIcon from '@/shared/components/AppIcon.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { changeCurrentUserPassword, updateCurrentUser } from '@/modules/auth/services/auth.service'
import { authStore, refreshCurrentUser } from '@/modules/auth/store'
import PasswordChangeForm from '../components/PasswordChangeForm.vue'
import ProfileBasicForm from '../components/ProfileBasicForm.vue'
import { providerPresets, quickNotes } from '@/modules/ai-config/constants/provider-presets'
import {
  createMyAiConfig,
  deleteMyAiConfig,
  fetchSystemDefaultAiConfig,
  listMyAiConfigs,
  setMyDefaultAiConfig,
  updateMyAiConfig,
} from '@/modules/ai-config/services/ai-config.service'
import type { AiConfigRead, AiConfigUpdatePayload } from '@/modules/ai-config/types/ai-config'

type Section = 'profile' | 'security' | 'ai-config' | 'ai-list'
const activeSection = ref<Section>('ai-config')

const sections = [
  { group: 'AI 设置', items: [
    { id: 'ai-config' as Section, label: '模型配置', desc: '新建或编辑 AI 模型', icon: 'spark' as const },
    { id: 'ai-list' as Section, label: '已有配置', desc: '查看和管理所有配置', icon: 'settings' as const },
  ]},
  { group: '账号', items: [
    { id: 'profile' as Section, label: '个人资料', desc: '更新用户名和邮箱', icon: 'user' as const },
    { id: 'security' as Section, label: '安全设置', desc: '修改登录密码', icon: 'lock' as const },
  ]},
]

// === Profile ===
const profileForm = reactive({ username: '', email: '' })
const passwordForm = reactive({ currentPassword: '', newPassword: '' })
const savingProfile = ref(false)
const changingPassword = ref(false)
const notice = ref('')
const error = ref('')

watch(() => authStore.user, (user) => {
  profileForm.username = user?.username ?? ''
  profileForm.email = user?.email ?? ''
}, { immediate: true })

function setNotice(msg: string) { notice.value = msg; error.value = '' }
function setError(msg: string) { error.value = msg; notice.value = '' }

async function saveProfile() {
  if (!authStore.token) return
  savingProfile.value = true; notice.value = ''; error.value = ''
  try {
    await updateCurrentUser(authStore.token, { username: profileForm.username.trim() || null, email: profileForm.email.trim() || null })
    await refreshCurrentUser()
    setNotice('个人信息已更新')
  } catch (err) { setError(err instanceof Error ? err.message : '更新失败') }
  finally { savingProfile.value = false }
}

async function savePassword() {
  if (!authStore.token) return
  changingPassword.value = true; notice.value = ''; error.value = ''
  try {
    await changeCurrentUserPassword(authStore.token, { current_password: passwordForm.currentPassword, new_password: passwordForm.newPassword })
    passwordForm.currentPassword = ''; passwordForm.newPassword = ''
    setNotice('密码修改成功')
  } catch (err) { setError(err instanceof Error ? err.message : '修改密码失败') }
  finally { changingPassword.value = false }
}

// === AI Config ===
const aiConfigs = ref<AiConfigRead[]>([])
const systemDefault = ref<AiConfigRead | null>(null)
const loadingConfigs = ref(false)
const savingConfig = ref(false)
const deletingConfigId = ref<number | null>(null)
const editingConfigId = ref<number | null>(null)

const aiForm = reactive({
  provider: 'openai', model_name: 'gpt-4.1-mini', api_key: '', base_url: 'https://api.openai.com/v1',
  temperature: 0.3, system_prompt: '', is_default: false,
})

function resetAiForm() {
  editingConfigId.value = null
  aiForm.provider = 'openai'; aiForm.model_name = 'gpt-4.1-mini'
  aiForm.api_key = ''; aiForm.base_url = 'https://api.openai.com/v1'
  aiForm.temperature = 0.3; aiForm.system_prompt = ''; aiForm.is_default = false
}

function applyPreset(provider: string) {
  const p = providerPresets.find((x) => x.provider === provider)
  if (!p) return
  aiForm.provider = p.provider; aiForm.model_name = p.model; aiForm.base_url = p.baseUrl
}

function startEditConfig(config: AiConfigRead) {
  editingConfigId.value = config.id; aiForm.provider = config.provider; aiForm.model_name = config.model_name
  aiForm.api_key = ''; aiForm.base_url = config.base_url ?? ''; aiForm.temperature = config.temperature
  aiForm.system_prompt = config.system_prompt ?? ''; aiForm.is_default = config.is_default
  activeSection.value = 'ai-config'
}

async function loadConfigs() {
  if (!authStore.token) return
  loadingConfigs.value = true
  try {
    const [my, def] = await Promise.all([listMyAiConfigs(authStore.token), fetchSystemDefaultAiConfig()])
    aiConfigs.value = my; systemDefault.value = def
  } catch {} finally { loadingConfigs.value = false }
}

async function saveAiConfig() {
  if (!authStore.token) return
  savingConfig.value = true; notice.value = ''; error.value = ''
  try {
    const payload = { provider: aiForm.provider.trim(), model_name: aiForm.model_name.trim(), api_key: aiForm.api_key.trim(), base_url: aiForm.base_url.trim() || null, temperature: aiForm.temperature, system_prompt: aiForm.system_prompt.trim() || null, is_default: aiForm.is_default }
    if (editingConfigId.value === null) { await createMyAiConfig(authStore.token, payload); setNotice('配置已创建') }
    else { await updateMyAiConfig(authStore.token, editingConfigId.value, payload as AiConfigUpdatePayload); setNotice('配置已更新') }
    resetAiForm(); await loadConfigs()
  } catch (err) { setError(err instanceof Error ? err.message : '保存失败') }
  finally { savingConfig.value = false }
}

async function removeAiConfig(id: number) {
  if (!authStore.token) return
  deletingConfigId.value = id
  try { await deleteMyAiConfig(authStore.token, id); if (editingConfigId.value === id) resetAiForm(); await loadConfigs(); setNotice('已删除') }
  catch (err) { setError(err instanceof Error ? err.message : '删除失败') }
  finally { deletingConfigId.value = null }
}

async function makeDefault(id: number) {
  if (!authStore.token) return
  try { await setMyDefaultAiConfig(authStore.token, id); await loadConfigs(); setNotice('已设为默认') }
  catch (err) { setError(err instanceof Error ? err.message : '设置失败') }
}

void loadConfigs()
</script>

<template>
  <div class="page">
    <!-- Sidebar -->
    <aside class="side">
      <!-- User -->
      <div class="side-user">
        <div class="avatar">{{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}</div>
        <div class="user-info">
          <strong>{{ authStore.user?.username || '用户' }}</strong>
          <span>{{ authStore.user?.email || '' }}</span>
        </div>
      </div>

      <!-- Nav -->
      <nav class="side-nav">
        <template v-for="group in sections" :key="group.group">
          <div class="nav-group-label">{{ group.group }}</div>
          <button
            v-for="item in group.items"
            :key="item.id"
            type="button"
            class="nav-item"
            :class="{ active: activeSection === item.id }"
            @click="activeSection = item.id"
          >
            <AppIcon :name="item.icon" :size="16" />
            <span>{{ item.label }}</span>
          </button>
        </template>
      </nav>

      <!-- Role -->
      <div class="side-bottom">
        <span class="role-tag">
          <AppIcon name="admin" :size="12" />
          {{ authStore.user?.roles.join(' · ') || '访客' }}
        </span>
      </div>
    </aside>

    <!-- Main -->
    <main class="main">
      <!-- Section Header -->
      <header class="section-header">
        <div class="section-crumb">
          <span>{{ sections.find(g => g.items.some(i => i.id === activeSection))?.group }}</span>
          <AppIcon name="chevron-right" :size="12" />
          <span class="crumb-current">
            {{ sections.flatMap(g => g.items).find(i => i.id === activeSection)?.label }}
          </span>
        </div>
        <h1>{{ sections.flatMap(g => g.items).find(i => i.id === activeSection)?.label }}</h1>
        <p>{{ sections.flatMap(g => g.items).find(i => i.id === activeSection)?.desc }}</p>
      </header>

      <NoticeBanner v-if="notice" :message="notice" tone="success" />
      <NoticeBanner v-if="error" :message="error" tone="error" />

      <!-- Profile -->
      <div v-if="activeSection === 'profile'" class="content">
        <div class="card">
          <div class="card-header">
            <h3>基本信息</h3>
            <p>这些信息会显示在你的个人主页上</p>
          </div>
          <div class="card-body">
            <ProfileBasicForm
              :username="profileForm.username"
              :email="profileForm.email"
              :saving="savingProfile"
              @update:username="profileForm.username = $event"
              @update:email="profileForm.email = $event"
              @submit="saveProfile"
            />
          </div>
        </div>
      </div>

      <!-- Security -->
      <div v-else-if="activeSection === 'security'" class="content">
        <div class="card">
          <div class="card-header">
            <h3>修改密码</h3>
            <p>为了账号安全，建议每 3 个月更新一次密码</p>
          </div>
          <div class="card-body">
            <PasswordChangeForm
              :current-password="passwordForm.currentPassword"
              :new-password="passwordForm.newPassword"
              :saving="changingPassword"
              @update:currentPassword="passwordForm.currentPassword = $event"
              @update:newPassword="passwordForm.newPassword = $event"
              @submit="savePassword"
            />
          </div>
        </div>
      </div>

      <!-- AI Config -->
      <div v-else-if="activeSection === 'ai-config'" class="content">
        <div class="card">
          <div class="card-header">
            <h3>{{ editingConfigId ? '编辑配置' : '新建配置' }}</h3>
            <p>选择服务商并填写参数，保存后批改将使用此配置</p>
          </div>
          <div class="card-body">
            <!-- Provider selector inline -->
            <div class="provider-selector">
              <span class="provider-label">服务商</span>
              <div class="provider-tabs">
                <button
                  v-for="preset in providerPresets"
                  :key="preset.provider"
                  type="button"
                  class="provider-tab"
                  :class="{ active: aiForm.provider === preset.provider }"
                  @click="applyPreset(preset.provider)"
                >
                  {{ preset.label }}
                </button>
              </div>
            </div>

            <!-- Form -->
            <AiConfigEditor
              :title="editingConfigId ? '编辑配置' : '新建配置'"
              :provider="aiForm.provider"
              :model-name="aiForm.model_name"
              :api-key="aiForm.api_key"
              :base-url="aiForm.base_url"
              :temperature="aiForm.temperature"
              :system-prompt="aiForm.system_prompt"
              :is-default="aiForm.is_default"
              :saving="savingConfig"
              submit-label="保存配置"
              reset-label="重置"
              @update:provider="aiForm.provider = $event"
              @update:modelName="aiForm.model_name = $event"
              @update:apiKey="aiForm.api_key = $event"
              @update:baseUrl="aiForm.base_url = $event"
              @update:temperature="aiForm.temperature = $event"
              @update:systemPrompt="aiForm.system_prompt = $event"
              @update:isDefault="aiForm.is_default = $event"
              @submit="saveAiConfig"
              @reset="resetAiForm"
            />
          </div>
        </div>
      </div>

      <!-- AI List -->
      <div v-else-if="activeSection === 'ai-list'" class="content">
        <div v-if="systemDefault" class="info-strip">
          <AppIcon name="info" :size="16" />
          <div>
            <strong>系统默认配置</strong>
            <span>{{ systemDefault.provider }} / {{ systemDefault.model_name }} · 温度 {{ systemDefault.temperature }}</span>
          </div>
        </div>

        <div v-if="loadingConfigs" class="placeholder">加载中...</div>
        <div v-else-if="aiConfigs.length === 0" class="empty-card">
          <div class="empty-icon">
            <AppIcon name="settings" :size="24" />
          </div>
          <h3>暂无个人配置</h3>
          <p>前往「模型配置」创建你的第一个配置</p>
          <button type="button" class="primary-btn" @click="activeSection = 'ai-config'">
            <AppIcon name="plus" :size="14" />
            创建配置
          </button>
        </div>

        <div v-else class="config-list">
          <article v-for="config in aiConfigs" :key="config.id" class="config-item" :class="{ default: config.is_default }">
            <div class="cfg-main">
              <div class="cfg-icon">
                <AppIcon name="spark" :size="18" />
              </div>
              <div class="cfg-info">
                <div class="cfg-title-row">
                  <strong>{{ config.model_name }}</strong>
                  <span v-if="config.is_default" class="cfg-default-tag">
                    <AppIcon name="check" :size="10" />
                    默认
                  </span>
                </div>
                <div class="cfg-meta">
                  <span>{{ config.provider }}</span>
                  <span class="dot">·</span>
                  <span>温度 {{ config.temperature }}</span>
                  <span v-if="config.base_url" class="dot">·</span>
                  <span v-if="config.base_url" class="cfg-url">{{ config.base_url }}</span>
                </div>
              </div>
            </div>
            <div class="cfg-actions">
              <button type="button" class="act-btn" @click="startEditConfig(config)">
                <AppIcon name="edit" :size="12" />
                编辑
              </button>
              <button type="button" class="act-btn" @click="makeDefault(config.id)">设默认</button>
              <button type="button" class="act-btn danger" :disabled="deletingConfigId === config.id" @click="removeAiConfig(config.id)">
                <AppIcon name="trash" :size="12" />
                删除
              </button>
            </div>
          </article>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.page {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: calc(100vh - 53px);
  background: var(--bg);
}

/* === Sidebar === */
.side {
  background: var(--paper);
  border-right: 1px solid var(--line);
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 53px;
  height: calc(100vh - 53px);
  overflow-y: auto;
}

.side-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 16px 14px;
  border-bottom: 1px solid var(--line-soft);
  margin-bottom: 10px;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-sans);
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
  letter-spacing: -0.02em;
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
  gap: 1px;
}

.user-info strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.user-info span {
  font-size: 11px;
  color: var(--support);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.user-info strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-info span {
  font-size: 11px;
  color: var(--support);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Nav */
.side-nav {
  flex: 1;
  padding: 0 8px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-group-label {
  padding: 14px 10px 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--support);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.nav-group-label:first-child {
  padding-top: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  background: transparent;
  border: none;
  text-align: left;
  width: 100%;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  color: var(--ink);
  background: var(--bg-soft);
}

.nav-item.active {
  color: var(--accent);
  background: var(--accent-soft);
  font-weight: 600;
}

.side-bottom {
  padding: 12px 16px 0;
  border-top: 1px solid var(--line-soft);
  margin-top: 12px;
}

.role-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-soft);
  border: 1px solid var(--line);
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* === Main === */
.main {
  padding: 32px 40px 64px;
  max-width: 960px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Section Header */
.section-header {
  display: flex;
  flex-direction: column;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 4px;
}

.section-crumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--support);
  margin-bottom: 10px;
}

.crumb-current {
  color: var(--ink);
  font-weight: 500;
}

.section-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-sans);
  margin: 0 0 4px;
  text-align: left;
}

.section-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
  text-align: left;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Card */
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
  font-family: var(--font-sans);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}

.card-header p {
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
}

.card-body {
  padding: 24px 28px 28px;
}

/* Override sub-card inside card-body */
.card-body :deep(.sub-card) {
  border: none;
  padding: 0;
  box-shadow: none;
  background: transparent;
  gap: 0;
}

.card-body :deep(.sub-card h3) {
  display: none;
}

.card-body :deep(.field) {
  display: grid;
  gap: 7px;
  margin-bottom: 18px;
}

.card-body :deep(.field:last-of-type) {
  margin-bottom: 0;
}

.card-body :deep(.field label) {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: 0.01em;
}

.card-body :deep(.field input),
.card-body :deep(.field textarea) {
  padding: 9px 13px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper);
  font-size: 13px;
  color: var(--ink);
  box-shadow: none;
  transition: all var(--transition-fast);
}

.card-body :deep(.field input:hover),
.card-body :deep(.field textarea:hover) {
  border-color: var(--line-strong);
}

.card-body :deep(.field input:focus),
.card-body :deep(.field textarea:focus) {
  border-color: var(--accent);
  box-shadow: var(--ring);
}

.card-body :deep(.primary-button) {
  padding: 8px 18px;
  width: auto;
  margin-top: 20px;
  font-size: 13px;
  min-height: 34px;
  justify-self: start;
}

.card-body :deep(.ghost-button) {
  padding: 8px 18px;
  font-size: 13px;
  min-height: 34px;
  justify-self: start;
}

.card-body :deep(.checkbox-row) {
  margin-top: 12px;
  padding: 0;
  border: none;
  background: transparent;
  min-height: auto;
}

/* Provider Selector */
.provider-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line-soft);
}

.provider-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  flex-shrink: 0;
}

.provider-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.provider-tab {
  padding: 6px 14px;
  border: 1px solid var(--line);
  border-radius: 100px;
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.provider-tab:hover {
  border-color: var(--line-strong);
  color: var(--ink);
}

.provider-tab.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

/* Info Strip */
.info-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: var(--accent-soft);
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: var(--radius-lg);
  color: var(--accent-deep);
}

.info-strip > div {
  display: flex;
  flex-direction: column;
}

.info-strip strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-deep);
}

.info-strip span {
  font-size: 12px;
  color: var(--accent-deep);
  opacity: 0.8;
}

/* Placeholder */
.placeholder {
  text-align: center;
  padding: 48px 24px;
  color: var(--support);
  font-size: 13px;
}

/* Empty card */
.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 56px 24px;
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-xl);
}

.empty-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--bg-soft);
  color: var(--support);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
}

.empty-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 4px;
}

.empty-card p {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 20px;
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  transition: background var(--transition-fast);
}

.primary-btn:hover {
  background: var(--accent-deep);
}

/* Config List */
.config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-fast);
}

.config-item:hover {
  border-color: var(--line-strong);
  box-shadow: var(--shadow);
}

.config-item.default {
  border-left: 3px solid var(--accent);
}

.cfg-main {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex: 1;
}

.cfg-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cfg-info {
  min-width: 0;
  flex: 1;
}

.cfg-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.cfg-title-row strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.cfg-default-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  border-radius: 100px;
}

.cfg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted);
}

.cfg-meta .dot {
  color: var(--line-strong);
}

.cfg-url {
  font-family: var(--font-mono);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.cfg-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.act-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper);
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.act-btn:hover:not(:disabled) {
  color: var(--accent);
  border-color: var(--accent);
}

.act-btn.danger:hover:not(:disabled) {
  color: var(--danger);
  border-color: var(--danger);
}

/* Responsive */
@media (max-width: 900px) {
  .page {
    grid-template-columns: 1fr;
  }

  .side {
    position: static;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--line);
  }

  .main {
    padding: 24px 20px;
  }

  .config-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .cfg-actions {
    width: 100%;
  }
}
</style>
