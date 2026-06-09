<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

import AiConfigEditor from '@/features/ai-config/components/AiConfigEditor.vue'
import AppIcon from '@/shared/components/AppIcon.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { updateCurrentUser } from '@/modules/auth/services/auth.service'
import { authStore, refreshCurrentUser } from '@/modules/auth/store'
import { providerPresets } from '@/modules/ai-config/constants/provider-presets'
import {
  createMyAiConfig,
  deleteMyAiConfig,
  fetchSystemDefaultAiConfig,
  listMyAiConfigs,
  setMyDefaultAiConfig,
  updateMyAiConfig,
} from '@/modules/ai-config/services/ai-config.service'
import type { AiConfigRead, AiConfigUpdatePayload } from '@/modules/ai-config/types/ai-config'
import ProfileBasicForm from '../components/ProfileBasicForm.vue'

// === Profile ===
const profileForm = reactive({ username: '', email: '' })
const savingProfile = ref(false)
const notice = ref('')
const error = ref('')

watch(() => authStore.user, (user) => {
  profileForm.username = user?.username ?? ''
  profileForm.email = user?.email ?? ''
}, { immediate: true })

async function saveProfile() {
  if (!authStore.token) return
  savingProfile.value = true; notice.value = ''; error.value = ''
  try {
    await updateCurrentUser(authStore.token, { username: profileForm.username.trim() || null, email: profileForm.email.trim() || null })
    await refreshCurrentUser()
    notice.value = '个人信息已更新'
  } catch (err) { error.value = err instanceof Error ? err.message : '更新失败' }
  finally { savingProfile.value = false }
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
    if (editingConfigId.value === null) { await createMyAiConfig(authStore.token, payload); notice.value = '配置已创建' }
    else { await updateMyAiConfig(authStore.token, editingConfigId.value, payload as AiConfigUpdatePayload); notice.value = '配置已更新' }
    resetAiForm(); await loadConfigs()
  } catch (err) { error.value = err instanceof Error ? err.message : '保存失败' }
  finally { savingConfig.value = false }
}

async function removeAiConfig(id: number) {
  if (!authStore.token) return
  deletingConfigId.value = id
  try { await deleteMyAiConfig(authStore.token, id); if (editingConfigId.value === id) resetAiForm(); await loadConfigs(); notice.value = '已删除' }
  catch (err) { error.value = err instanceof Error ? err.message : '删除失败' }
  finally { deletingConfigId.value = null }
}

async function makeDefault(id: number) {
  if (!authStore.token) return
  try { await setMyDefaultAiConfig(authStore.token, id); await loadConfigs(); notice.value = '已设为默认' }
  catch (err) { error.value = err instanceof Error ? err.message : '设置失败' }
}

void loadConfigs()
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <h1>个人资料</h1>
      <p>管理你的账号信息和 AI 模型配置</p>
    </header>

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <!-- Section 1: Basic Info -->
    <section class="section">
      <div class="section-title">
        <div class="section-icon"><AppIcon name="user" :size="16" /></div>
        <div>
          <h2>基本信息</h2>
          <p>这些信息会显示在你的个人主页上</p>
        </div>
      </div>
      <div class="card">
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
    </section>

    <!-- Divider -->
    <div class="divider"></div>

    <!-- Section 2: AI Config -->
    <section class="section">
      <div class="section-title">
        <div class="section-icon accent"><AppIcon name="spark" :size="16" /></div>
        <div>
          <h2>AI 模型配置</h2>
          <p>选择服务商并填写参数，保存后批改将使用此配置</p>
        </div>
      </div>

      <!-- Editor Card -->
      <div class="card">
        <div class="card-header">
          <h3>{{ editingConfigId ? '编辑配置' : '新建配置' }}</h3>
          <button v-if="editingConfigId" type="button" class="link-btn" @click="resetAiForm">取消编辑</button>
        </div>
        <div class="card-body">
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
              >{{ preset.label }}</button>
            </div>
          </div>
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

      <!-- System Default -->
      <div v-if="systemDefault" class="info-strip">
        <AppIcon name="info" :size="16" />
        <div>
          <strong>系统默认配置</strong>
          <span>{{ systemDefault.provider }} / {{ systemDefault.model_name }} · 温度 {{ systemDefault.temperature }}</span>
        </div>
      </div>

      <!-- Config List -->
      <div class="list-header">
        <h3>已有配置</h3>
        <span class="list-count">{{ aiConfigs.length }} 个</span>
      </div>

      <div v-if="loadingConfigs" class="placeholder">加载中...</div>
      <div v-else-if="aiConfigs.length === 0" class="empty-card">
        <div class="empty-icon"><AppIcon name="settings" :size="24" /></div>
        <h3>暂无个人配置</h3>
        <p>上方创建你的第一个配置</p>
      </div>
      <div v-else class="config-list">
        <article v-for="config in aiConfigs" :key="config.id" class="config-item" :class="{ default: config.is_default }">
          <div class="cfg-main">
            <div class="cfg-icon"><AppIcon name="spark" :size="18" /></div>
            <div class="cfg-info">
              <div class="cfg-title-row">
                <strong>{{ config.model_name }}</strong>
                <span v-if="config.is_default" class="cfg-default-tag"><AppIcon name="check" :size="10" /> 默认</span>
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
            <button type="button" class="act-btn" @click="startEditConfig(config)"><AppIcon name="edit" :size="12" /> 编辑</button>
            <button type="button" class="act-btn" @click="makeDefault(config.id)">设默认</button>
            <button type="button" class="act-btn danger" :disabled="deletingConfigId === config.id" @click="removeAiConfig(config.id)"><AppIcon name="trash" :size="12" /> 删除</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Page Header */
.page-header {
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 4px;
}

.page-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
}

/* Section */
.section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--bg-soft);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.section-icon.accent {
  background: var(--accent-soft);
  color: var(--accent);
}

.section-title h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 2px;
}

.section-title p {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
}

/* Divider */
.divider {
  height: 1px;
  background: var(--line);
  margin: 8px 0;
}

/* Card */
.card {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.card-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--line-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin: 0;
}

.card-body {
  padding: 24px;
}

.link-btn {
  background: none;
  border: none;
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.link-btn:hover {
  color: var(--accent);
  background: var(--accent-soft);
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

.provider-tab:hover { border-color: var(--line-strong); color: var(--ink); }
.provider-tab.active { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); font-weight: 600; }

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

.info-strip > div { display: flex; flex-direction: column; }
.info-strip strong { font-size: 13px; font-weight: 600; }
.info-strip span { font-size: 12px; opacity: 0.8; }

/* List Header */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.list-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  margin: 0;
}

.list-count {
  font-size: 12px;
  color: var(--support);
  padding: 2px 10px;
  background: var(--bg-soft);
  border-radius: 100px;
}

/* Placeholder & Empty */
.placeholder {
  text-align: center;
  padding: 48px 24px;
  color: var(--support);
  font-size: 13px;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
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

.empty-card h3 { font-size: 15px; font-weight: 600; color: var(--ink); margin-bottom: 4px; }
.empty-card p { font-size: 13px; color: var(--muted); margin: 0; }

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

.config-item:hover { border-color: var(--line-strong); box-shadow: var(--shadow); }
.config-item.default { border-left: 3px solid var(--accent); }

.cfg-main { display: flex; align-items: center; gap: 14px; min-width: 0; flex: 1; }
.cfg-icon { width: 40px; height: 40px; border-radius: 10px; background: var(--accent-soft); color: var(--accent); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cfg-info { min-width: 0; flex: 1; }
.cfg-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.cfg-title-row strong { font-size: 14px; font-weight: 600; color: var(--ink); }
.cfg-default-tag { display: inline-flex; align-items: center; gap: 3px; padding: 2px 8px; background: var(--accent); color: #fff; font-size: 10px; font-weight: 600; border-radius: 100px; }
.cfg-meta { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted); }
.cfg-meta .dot { color: var(--line-strong); }
.cfg-url { font-family: var(--font-mono); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }

.cfg-actions { display: flex; gap: 6px; flex-shrink: 0; }
.act-btn { display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--paper); color: var(--muted); font-size: 12px; font-weight: 500; transition: all var(--transition-fast); }
.act-btn:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
.act-btn.danger:hover:not(:disabled) { color: var(--danger); border-color: var(--danger); }
</style>
