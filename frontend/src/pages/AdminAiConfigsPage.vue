<script setup lang="ts">
import { defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'

import {
  createAdminSystemAiConfig,
  deleteAdminSystemAiConfig,
  listAdminSystemAiConfigs,
  setAdminSystemDefaultAiConfig,
  updateAdminSystemAiConfig,
} from '../services/admin_ai_configs'
import type { AiConfigCreatePayload, AiConfigRead, AiConfigUpdatePayload } from '../services/ai_configs'

const props = defineProps<{
  token: string | null
}>()

const configs = ref<AiConfigRead[]>([])
const loading = ref(false)
const saving = ref(false)
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
const SectionHeader = defineAsyncComponent(() => import('../components/SectionHeader.vue'))
const NoticeBanner = defineAsyncComponent(() => import('../components/NoticeBanner.vue'))
const AdminAiConfigsList = defineAsyncComponent(() => import('../components/AdminAiConfigsList.vue'))
const AiConfigEditor = defineAsyncComponent(() => import('../components/AiConfigEditor.vue'))

function resetMessages() {
  notice.value = ''
  error.value = ''
}

function setNotice(message: string) {
  notice.value = message
  error.value = ''
}

function setError(message: string) {
  error.value = message
  notice.value = ''
}

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

function fillForm(config: AiConfigRead) {
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
  if (!props.token) {
    configs.value = []
    return
  }

  loading.value = true
  try {
    configs.value = await listAdminSystemAiConfigs(props.token)
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载系统 AI 配置失败')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  if (!props.token) {
    return
  }

  saving.value = true
  resetMessages()
  try {
    const payload: AiConfigCreatePayload = {
      provider: form.provider.trim(),
      model_name: form.model_name.trim(),
      api_key: form.api_key.trim(),
      base_url: form.base_url?.trim() || null,
      temperature: form.temperature,
      system_prompt: form.system_prompt?.trim() || null,
      is_default: form.is_default,
    }

    if (editingConfigId.value === null) {
      await createAdminSystemAiConfig(props.token, payload)
      setNotice('已创建系统 AI 配置')
    } else {
      const updatePayload: AiConfigUpdatePayload = {
        ...payload,
        api_key: payload.api_key,
      }
      await updateAdminSystemAiConfig(props.token, editingConfigId.value, updatePayload)
      setNotice('已更新系统 AI 配置')
    }

    resetForm()
    await loadConfigs()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存系统 AI 配置失败')
  } finally {
    saving.value = false
  }
}

async function removeConfig(configId: number) {
  if (!props.token) {
    return
  }

  deletingConfigId.value = configId
  resetMessages()
  try {
    await deleteAdminSystemAiConfig(props.token, configId)
    if (editingConfigId.value === configId) {
      resetForm()
    }
    await loadConfigs()
    setNotice('已删除系统 AI 配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除系统 AI 配置失败')
  } finally {
    deletingConfigId.value = null
  }
}

async function makeDefault(configId: number) {
  if (!props.token) {
    return
  }

  resetMessages()
  try {
    await setAdminSystemDefaultAiConfig(props.token, configId)
    await loadConfigs()
    setNotice('已设为系统默认配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '设置系统默认配置失败')
  }
}

watch(
  () => props.token,
  () => {
    resetMessages()
    resetForm()
    void loadConfigs()
  },
  { immediate: true },
)

onMounted(() => {
  void loadConfigs()
})
</script>

<script lang="ts">
export default {
  name: 'AdminAiConfigsPage',
}
</script>

<template>
  <div class="page-card page-section">
    <SectionHeader kicker="管理员后台" title="系统 AI 配置管理" hint="支持系统级配置列表、创建、更新、删除与默认设置" />

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <AiConfigEditor
      :title="editingConfigId ? '编辑系统配置' : '创建系统配置'"
      :provider="form.provider"
      :model-name="form.model_name"
      :api-key="form.api_key"
      :base-url="form.base_url || ''"
      :temperature="form.temperature || 0.3"
      :system-prompt="form.system_prompt || ''"
      :is-default="Boolean(form.is_default)"
      :saving="saving"
      :submit-label="editingConfigId ? '更新配置' : '创建配置'"
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

    <section class="sub-card">
      <div class="section-header compact">
        <h3>系统配置列表</h3>
        <span class="workspace-hint" v-if="loading">加载中...</span>
      </div>

      <AdminAiConfigsList :configs="configs" :loading="loading" :deleting-config-id="deletingConfigId" @edit="fillForm" @delete="removeConfig" @default="makeDefault" />
    </section>
  </div>
</template>
