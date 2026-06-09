<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import AiConfigEditor from '@/features/ai-config/components/AiConfigEditor.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { authStore } from '@/modules/auth/store'
import { providerPresets, quickNotes } from '../constants/provider-presets'
import {
  createMyAiConfig,
  deleteMyAiConfig,
  fetchSystemDefaultAiConfig,
  listMyAiConfigs,
  setMyDefaultAiConfig,
  updateMyAiConfig,
} from '../services/ai-config.service'
import type { AiConfigRead, AiConfigUpdatePayload } from '../types/ai-config'

const configs = ref<AiConfigRead[]>([])
const systemDefault = ref<AiConfigRead | null>(null)
const loadingConfigs = ref(false)
const savingConfig = ref(false)
const deletingConfigId = ref<number | null>(null)
const editingConfigId = ref<number | null>(null)
const notice = ref('')
const error = ref('')

const form = reactive({
  provider: 'openai',
  model_name: 'gpt-4.1-mini',
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  temperature: 0.3,
  system_prompt: '',
  is_default: false,
})

function resetMessages() { notice.value = ''; error.value = '' }
function setNotice(msg: string) { notice.value = msg; error.value = '' }
function setError(msg: string) { error.value = msg; notice.value = '' }

function resetForm() {
  editingConfigId.value = null
  form.provider = 'openai'
  form.model_name = 'gpt-4.1-mini'
  form.api_key = ''
  form.base_url = 'https://api.openai.com/v1'
  form.temperature = 0.3
  form.system_prompt = ''
  form.is_default = false
}

function applyPreset(provider: string) {
  const preset = providerPresets.find((p) => p.provider === provider)
  if (!preset) return
  form.provider = preset.provider
  form.model_name = preset.model
  form.base_url = preset.baseUrl
}

function startEditConfig(config: AiConfigRead) {
  editingConfigId.value = config.id
  form.provider = config.provider
  form.model_name = config.model_name
  form.api_key = ''
  form.base_url = config.base_url ?? ''
  form.temperature = config.temperature
  form.system_prompt = config.system_prompt ?? ''
  form.is_default = config.is_default
}

async function loadConfigs() {
  if (!authStore.token) { configs.value = []; systemDefault.value = null; return }
  loadingConfigs.value = true
  try {
    const [myConfigs, defaultConfig] = await Promise.all([
      listMyAiConfigs(authStore.token),
      fetchSystemDefaultAiConfig(),
    ])
    configs.value = myConfigs
    systemDefault.value = defaultConfig
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载 AI 配置失败')
  } finally { loadingConfigs.value = false }
}

async function saveConfig() {
  if (!authStore.token) return
  savingConfig.value = true
  resetMessages()
  try {
    const payload = {
      provider: form.provider.trim(),
      model_name: form.model_name.trim(),
      api_key: form.api_key.trim(),
      base_url: form.base_url.trim() || null,
      temperature: form.temperature,
      system_prompt: form.system_prompt.trim() || null,
      is_default: form.is_default,
    }
    if (editingConfigId.value === null) {
      await createMyAiConfig(authStore.token, payload)
      setNotice('已创建个人 AI 配置')
    } else {
      await updateMyAiConfig(authStore.token, editingConfigId.value, payload as AiConfigUpdatePayload)
      setNotice('已更新个人 AI 配置')
    }
    resetForm()
    await loadConfigs()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存 AI 配置失败')
  } finally { savingConfig.value = false }
}

async function removeAiConfig(configId: number) {
  if (!authStore.token) return
  deletingConfigId.value = configId
  resetMessages()
  try {
    await deleteMyAiConfig(authStore.token, configId)
    if (editingConfigId.value === configId) resetForm()
    await loadConfigs()
    setNotice('已删除个人 AI 配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除 AI 配置失败')
  } finally { deletingConfigId.value = null }
}

async function makeDefaultAiConfig(configId: number) {
  if (!authStore.token) return
  resetMessages()
  try {
    await setMyDefaultAiConfig(authStore.token, configId)
    await loadConfigs()
    setNotice('已设为个人默认配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '设置默认配置失败')
  }
}

void loadConfigs()
</script>

<template>
  <div class="config-page">
    <div class="shell">
      <!-- Breadcrumb -->
      <nav class="breadcrumb">
        <RouterLink to="/profile" class="breadcrumb-link">← 返回个人中心</RouterLink>
      </nav>

      <!-- Header -->
      <header class="page-header">
        <h1>AI 模型配置</h1>
        <p class="page-desc">创建默认配置后，练习批改会直接沿用你的个人配置。</p>
      </header>

      <NoticeBanner v-if="notice" :message="notice" tone="success" class="notice-gap" />
      <NoticeBanner v-if="error" :message="error" tone="error" class="notice-gap" />

      <div class="layout">
        <!-- Main -->
        <div class="main-col">
          <!-- Editor -->
          <AiConfigEditor
            :title="editingConfigId ? '编辑配置' : '创建配置'"
            :provider="form.provider"
            :model-name="form.model_name"
            :api-key="form.api_key"
            :base-url="form.base_url"
            :temperature="form.temperature"
            :system-prompt="form.system_prompt"
            :is-default="form.is_default"
            :saving="savingConfig"
            submit-label="保存配置"
            reset-label="重置"
            @update:provider="form.provider = $event"
            @update:modelName="form.model_name = $event"
            @update:apiKey="form.api_key = $event"
            @update:baseUrl="form.base_url = $event"
            @update:temperature="form.temperature = $event"
            @update:systemPrompt="form.system_prompt = $event"
            @update:isDefault="form.is_default = $event"
            @submit="saveConfig"
            @reset="resetForm"
          />

          <!-- Config List -->
          <section class="card">
            <div class="card-head">
              <h3>我的配置</h3>
              <span v-if="loadingConfigs" class="hint">加载中...</span>
            </div>

            <div v-if="systemDefault" class="default-info">
              <span class="default-label">系统默认</span>
              <span class="default-value">{{ systemDefault.provider }} / {{ systemDefault.model_name }} / 温度 {{ systemDefault.temperature }}</span>
            </div>

            <p v-if="configs.length === 0" class="empty-text">还没有个人配置，先创建一个。</p>

            <div v-else class="config-list">
              <article v-for="config in configs" :key="config.id" class="config-row">
                <div class="config-row-main">
                  <div class="config-row-title">
                    <strong>{{ config.provider }} / {{ config.model_name }}</strong>
                    <span v-if="config.is_default" class="badge">默认</span>
                  </div>
                  <p class="config-row-detail">
                    接口：{{ config.base_url || '未填写' }} · 温度：{{ config.temperature }}
                  </p>
                </div>
                <div class="config-row-actions">
                  <button type="button" class="action-btn" @click="startEditConfig(config)">编辑</button>
                  <button type="button" class="action-btn" :disabled="deletingConfigId === config.id" @click="removeAiConfig(config.id)">
                    {{ deletingConfigId === config.id ? '...' : '删除' }}
                  </button>
                  <button type="button" class="action-btn action-btn-accent" @click="makeDefaultAiConfig(config.id)">设默认</button>
                </div>
              </article>
            </div>
          </section>
        </div>

        <!-- Sidebar -->
        <aside class="side-col">
          <section class="card">
            <h3 class="card-title">服务商模板</h3>
            <div class="preset-list">
              <button
                v-for="preset in providerPresets"
                :key="preset.provider"
                type="button"
                class="preset-item"
                :class="{ active: form.provider === preset.provider }"
                @click="applyPreset(preset.provider)"
              >
                <strong>{{ preset.label }}</strong>
                <span>{{ preset.model || '自定义' }}</span>
              </button>
            </div>
          </section>

          <section class="card">
            <h3 class="card-title">使用提示</h3>
            <ul class="tips-list">
              <li v-for="item in quickNotes" :key="item">{{ item }}</li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-page {
  padding: 24px 0 64px;
}

.breadcrumb {
  margin-bottom: 20px;
}

.breadcrumb-link {
  font-size: 13px;
  font-weight: 500;
  color: var(--muted);
  transition: color var(--transition-fast);
}

.breadcrumb-link:hover {
  color: var(--accent);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-sans);
  color: var(--ink);
  margin-bottom: 4px;
}

.page-desc {
  font-size: 13px;
  color: var(--muted);
}

.notice-gap {
  margin-bottom: 16px;
}

/* Layout */
.layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 20px;
  align-items: start;
}

.main-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.side-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 72px;
}

/* Card */
.card {
  padding: 20px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-head h3,
.card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-sans);
}

.card-title {
  margin-bottom: 12px;
}

.hint {
  font-size: 12px;
  color: var(--support);
}

/* Default Info */
.default-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  background: var(--bg-soft);
  border-radius: var(--radius-md);
  margin-bottom: 14px;
}

.default-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.default-value {
  font-size: 13px;
  color: var(--muted);
}

.empty-text {
  font-size: 13px;
  color: var(--muted);
  text-align: center;
  padding: 24px 0;
}

/* Config List */
.config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-fast);
}

.config-row:hover {
  border-color: var(--line-strong);
}

.config-row-main {
  min-width: 0;
  flex: 1;
}

.config-row-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.config-row-title strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.badge {
  padding: 2px 8px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10px;
  font-weight: 600;
  border-radius: 100px;
}

.config-row-detail {
  font-size: 12px;
  color: var(--muted);
}

.config-row-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.action-btn {
  padding: 5px 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--paper);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  border-color: var(--line-strong);
  color: var(--ink);
}

.action-btn-accent {
  border-color: var(--accent);
  color: var(--accent);
}

.action-btn-accent:hover {
  background: var(--accent-soft);
}

/* Presets */
.preset-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.preset-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--paper);
  text-align: left;
  transition: all var(--transition-fast);
}

.preset-item:hover {
  border-color: var(--line-strong);
}

.preset-item.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.preset-item strong {
  font-size: 13px;
  color: var(--ink);
}

.preset-item span {
  font-size: 11px;
  color: var(--muted);
}

/* Tips */
.tips-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 16px;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.6;
}

/* Responsive */
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .side-col {
    position: static;
  }
}

@media (max-width: 640px) {
  .config-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .config-row-actions {
    width: 100%;
  }
}
</style>
