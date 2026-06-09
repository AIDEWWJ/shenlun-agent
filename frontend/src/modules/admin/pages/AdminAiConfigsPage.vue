<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import AiConfigEditor from '@/features/ai-config/components/AiConfigEditor.vue'
import AppIcon from '@/shared/components/AppIcon.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { authStore } from '@/modules/auth/store'
import AdminAiConfigsList from '../components/AdminAiConfigsList.vue'
import {
  createAdminSystemAiConfig,
  deleteAdminSystemAiConfig,
  listAdminSystemAiConfigs,
  setAdminSystemDefaultAiConfig,
  updateAdminSystemAiConfig,
} from '../services/admin-ai-config.service'

const configs = ref([])
const loading = ref(false)
const saving = ref(false)
const deletingConfigId = ref<number | null>(null)
const editingConfigId = ref<number | null>(null)
const notice = ref('')
const error = ref('')

const form = reactive({
  provider: 'openai', model_name: 'gpt-4.1-mini', api_key: '',
  base_url: 'https://api.openai.com/v1', temperature: 0.3,
  system_prompt: '', is_default: false,
})

function resetMessages() { notice.value = ''; error.value = '' }
function setNotice(msg: string) { notice.value = msg; error.value = '' }
function setError(msg: string) { error.value = msg; notice.value = '' }

function resetForm() {
  editingConfigId.value = null
  form.provider = 'openai'; form.model_name = 'gpt-4.1-mini'
  form.api_key = ''; form.base_url = 'https://api.openai.com/v1'
  form.temperature = 0.3; form.system_prompt = ''; form.is_default = false
}

function fillForm(config: { id: number; provider: string; model_name: string; base_url: string | null; temperature: number; system_prompt: string | null; is_default: boolean }) {
  editingConfigId.value = config.id
  form.provider = config.provider; form.model_name = config.model_name
  form.api_key = ''; form.base_url = config.base_url ?? ''
  form.temperature = config.temperature; form.system_prompt = config.system_prompt ?? ''
  form.is_default = config.is_default
}

async function loadConfigs() {
  if (!authStore.token) return
  loading.value = true
  try { configs.value = await listAdminSystemAiConfigs(authStore.token) }
  catch (err) { setError(err instanceof Error ? err.message : '加载系统 AI 配置失败') }
  finally { loading.value = false }
}

async function saveConfig() {
  if (!authStore.token) return
  saving.value = true; resetMessages()
  try {
    const payload = { provider: form.provider.trim(), model_name: form.model_name.trim(), api_key: form.api_key.trim(), base_url: form.base_url?.trim() || null, temperature: form.temperature, system_prompt: form.system_prompt?.trim() || null, is_default: form.is_default }
    if (editingConfigId.value === null) { await createAdminSystemAiConfig(authStore.token, payload); setNotice('已创建系统 AI 配置') }
    else { await updateAdminSystemAiConfig(authStore.token, editingConfigId.value, payload); setNotice('已更新系统 AI 配置') }
    resetForm(); await loadConfigs()
  } catch (err) { setError(err instanceof Error ? err.message : '保存系统 AI 配置失败') }
  finally { saving.value = false }
}

async function removeConfig(configId: number) {
  if (!authStore.token) return
  deletingConfigId.value = configId; resetMessages()
  try { await deleteAdminSystemAiConfig(authStore.token, configId); if (editingConfigId.value === configId) resetForm(); await loadConfigs(); setNotice('已删除系统 AI 配置') }
  catch (err) { setError(err instanceof Error ? err.message : '删除系统 AI 配置失败') }
  finally { deletingConfigId.value = null }
}

async function makeDefault(configId: number) {
  if (!authStore.token) return
  resetMessages()
  try { await setAdminSystemDefaultAiConfig(authStore.token, configId); await loadConfigs(); setNotice('已设为系统默认配置') }
  catch (err) { setError(err instanceof Error ? err.message : '设置系统默认配置失败') }
}

onMounted(() => { void loadConfigs() })
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <div>
        <h1>系统 AI 配置</h1>
        <p>管理系统级 AI 模型策略及默认配置</p>
      </div>
    </header>

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <div class="admin-grid">
      <!-- Editor -->
      <div class="card">
        <div class="card-header">
          <h3>{{ editingConfigId ? '编辑模型' : '创建模型' }}</h3>
          <button v-if="editingConfigId" type="button" class="link-btn" @click="resetForm">取消</button>
        </div>
        <div class="card-body">
          <AiConfigEditor
            :title="editingConfigId ? '编辑模型' : '创建模型'"
            :provider="form.provider"
            :model-name="form.model_name"
            :api-key="form.api_key"
            :base-url="form.base_url || ''"
            :temperature="form.temperature || 0.3"
            :system-prompt="form.system_prompt || ''"
            :is-default="Boolean(form.is_default)"
            :saving="saving"
            :submit-label="editingConfigId ? '更新' : '创建'"
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
        </div>
      </div>

      <!-- List -->
      <div class="card">
        <div class="card-header">
          <h3>系统配置列表</h3>
          <span v-if="loading" class="loading-text">加载中...</span>
        </div>
        <div class="card-body">
          <AdminAiConfigsList :configs="configs" :loading="loading" :deleting-config-id="deletingConfigId" @edit="fillForm" @delete="removeConfig" @default="makeDefault" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--line);
}

.page-header h1 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0 0 4px; }
.page-header p { font-size: 13px; color: var(--muted); margin: 0; }

.admin-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
}

.card { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl); overflow: hidden; }
.card-header { padding: 16px 24px; border-bottom: 1px solid var(--line-soft); display: flex; align-items: center; justify-content: space-between; }
.card-header h3 { font-size: 14px; font-weight: 600; color: var(--ink); margin: 0; }
.card-body { padding: 24px; }

.link-btn { background: none; border: none; color: var(--muted); font-size: 12px; cursor: pointer; padding: 4px 8px; border-radius: var(--radius-md); transition: all var(--transition-fast); }
.link-btn:hover { color: var(--accent); background: var(--accent-soft); }

.loading-text { font-size: 12px; color: var(--support); }

@media (max-width: 900px) {
  .admin-grid { grid-template-columns: 1fr; }
}
</style>
