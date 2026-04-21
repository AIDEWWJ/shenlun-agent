<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, reactive, ref, watch } from 'vue'

import { authStore, refreshCurrentUser } from '../stores/auth'
import {
  changeCurrentUserPassword,
  updateCurrentUser,
  type PasswordChangePayload,
  type ProfileUpdatePayload,
} from '../services/auth'
import {
  createMyAiConfig,
  deleteMyAiConfig,
  fetchSystemDefaultAiConfig,
  listMyAiConfigs,
  setMyDefaultAiConfig,
  updateMyAiConfig,
  type AiConfigCreatePayload,
  type AiConfigRead,
  type AiConfigUpdatePayload,
} from '../services/ai_configs'

const props = defineProps<{
  token: string | null
}>()

const profileForm = reactive({
  username: '',
  email: '',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
})

const aiConfigForm = reactive({
  provider: 'openai',
  model_name: 'gpt-4.1-mini',
  api_key: '',
  base_url: 'https://api.openai.com/v1',
  temperature: 0.3,
  system_prompt: '',
  is_default: false,
})

const configs = ref<AiConfigRead[]>([])
const systemDefault = ref<AiConfigRead | null>(null)
const loadingConfigs = ref(false)
const savingProfile = ref(false)
const changingPassword = ref(false)
const savingConfig = ref(false)
const deletingConfigId = ref<number | null>(null)
const editingConfigId = ref<number | null>(null)
const notice = ref('')
const error = ref('')

const isEditingConfig = computed(() => editingConfigId.value !== null)
const tokenPreview = computed(() => {
  if (!props.token) {
    return '未登录'
  }

  return '已登录'
})
const UserIdentityCard = defineAsyncComponent(() => import('../components/UserIdentityCard.vue'))
const SectionHeader = defineAsyncComponent(() => import('../components/SectionHeader.vue'))
const NoticeBanner = defineAsyncComponent(() => import('../components/NoticeBanner.vue'))
const ProfileBasicForm = defineAsyncComponent(() => import('../components/ProfileBasicForm.vue'))
const PasswordChangeForm = defineAsyncComponent(() => import('../components/PasswordChangeForm.vue'))
const AiConfigEditor = defineAsyncComponent(() => import('../components/AiConfigEditor.vue'))

function resetMessages() {
  notice.value = ''
  error.value = ''
}

function setError(message: string) {
  error.value = message
  notice.value = ''
}

function setNotice(message: string) {
  notice.value = message
  error.value = ''
}

function cloneCurrentUser() {
  profileForm.username = authStore.user?.username ?? ''
  profileForm.email = authStore.user?.email ?? ''
}

function resetAiForm() {
  editingConfigId.value = null
  aiConfigForm.provider = 'openai'
  aiConfigForm.model_name = 'gpt-4.1-mini'
  aiConfigForm.api_key = ''
  aiConfigForm.base_url = 'https://api.openai.com/v1'
  aiConfigForm.temperature = 0.3
  aiConfigForm.system_prompt = ''
  aiConfigForm.is_default = false
}

function startEditConfig(config: AiConfigRead) {
  editingConfigId.value = config.id
  aiConfigForm.provider = config.provider
  aiConfigForm.model_name = config.model_name
  aiConfigForm.api_key = ''
  aiConfigForm.base_url = config.base_url ?? ''
  aiConfigForm.temperature = config.temperature
  aiConfigForm.system_prompt = config.system_prompt ?? ''
  aiConfigForm.is_default = config.is_default
}

async function loadConfigs() {
  if (!props.token) {
    configs.value = []
    systemDefault.value = null
    return
  }

  loadingConfigs.value = true
  try {
    const [myConfigs, defaultConfig] = await Promise.all([
      listMyAiConfigs(props.token),
      fetchSystemDefaultAiConfig(),
    ])
    configs.value = myConfigs
    systemDefault.value = defaultConfig
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载 AI 配置失败')
  } finally {
    loadingConfigs.value = false
  }
}

async function saveProfile() {
  if (!props.token) {
    return
  }

  savingProfile.value = true
  resetMessages()
  try {
    await updateCurrentUser(props.token, {
      username: profileForm.username.trim() || null,
      email: profileForm.email.trim() || null,
    })
    await refreshCurrentUser()
    setNotice('个人信息已更新')
  } catch (err) {
    setError(err instanceof Error ? err.message : '更新个人信息失败')
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  if (!props.token) {
    return
  }

  changingPassword.value = true
  resetMessages()
  try {
    await changeCurrentUserPassword(props.token, {
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
    })
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    setNotice('密码修改成功')
  } catch (err) {
    setError(err instanceof Error ? err.message : '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

async function saveAiConfig() {
  if (!props.token) {
    return
  }

  savingConfig.value = true
  resetMessages()
  try {
    const payload = {
      provider: aiConfigForm.provider.trim(),
      model_name: aiConfigForm.model_name.trim(),
      api_key: aiConfigForm.api_key.trim(),
      base_url: aiConfigForm.base_url.trim() || null,
      temperature: aiConfigForm.temperature,
      system_prompt: aiConfigForm.system_prompt.trim() || null,
      is_default: aiConfigForm.is_default,
    }

    if (editingConfigId.value === null) {
      await createMyAiConfig(props.token, payload)
      setNotice('已创建个人 AI 配置')
    } else {
      await updateMyAiConfig(props.token, editingConfigId.value, payload as AiConfigUpdatePayload)
      setNotice('已更新个人 AI 配置')
    }

    resetAiForm()
    await loadConfigs()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存 AI 配置失败')
  } finally {
    savingConfig.value = false
  }
}

async function removeAiConfig(configId: number) {
  if (!props.token) {
    return
  }

  deletingConfigId.value = configId
  resetMessages()
  try {
    await deleteMyAiConfig(props.token, configId)
    if (editingConfigId.value === configId) {
      resetAiForm()
    }
    await loadConfigs()
    setNotice('已删除个人 AI 配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除 AI 配置失败')
  } finally {
    deletingConfigId.value = null
  }
}

async function makeDefaultAiConfig(configId: number) {
  if (!props.token) {
    return
  }

  resetMessages()
  try {
    await setMyDefaultAiConfig(props.token, configId)
    await loadConfigs()
    setNotice('已设为个人默认配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '设置默认配置失败')
  }
}

watch(
  () => props.token,
  () => {
    cloneCurrentUser()
    resetMessages()
    void loadConfigs()
  },
  { immediate: true },
)

watch(
  () => authStore.user,
  () => {
    cloneCurrentUser()
  },
  { immediate: true },
)

onMounted(() => {
  cloneCurrentUser()
})
</script>

<script lang="ts">
export default {
  name: 'UserProfilePage',
}
</script>

<template>
  <div class="page-card page-section">
    <SectionHeader kicker="个人中心" title="个人信息、密码与 AI 配置" hint="用户侧功能已接通后端接口" />

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <UserIdentityCard v-if="authStore.user" :user="authStore.user" :token-preview="tokenPreview" />

    <div class="profile-grid">
      <ProfileBasicForm
        :username="profileForm.username"
        :email="profileForm.email"
        :saving="savingProfile"
        @update:username="profileForm.username = $event"
        @update:email="profileForm.email = $event"
        @submit="saveProfile"
      />

      <PasswordChangeForm
        :current-password="passwordForm.currentPassword"
        :new-password="passwordForm.newPassword"
        :saving="changingPassword"
        @update:currentPassword="passwordForm.currentPassword = $event"
        @update:newPassword="passwordForm.newPassword = $event"
        @submit="savePassword"
      />
    </div>

    <AiConfigEditor
      :title="isEditingConfig ? '编辑个人 AI 配置' : '创建个人 AI 配置'"
      :provider="aiConfigForm.provider"
      :model-name="aiConfigForm.model_name"
      :api-key="aiConfigForm.api_key"
      :base-url="aiConfigForm.base_url"
      :temperature="aiConfigForm.temperature"
      :system-prompt="aiConfigForm.system_prompt"
      :is-default="aiConfigForm.is_default"
      :saving="savingConfig"
      submit-label="创建配置"
      reset-label="重置表单"
      @update:provider="aiConfigForm.provider = $event"
      @update:modelName="aiConfigForm.model_name = $event"
      @update:apiKey="aiConfigForm.api_key = $event"
      @update:baseUrl="aiConfigForm.base_url = $event"
      @update:temperature="aiConfigForm.temperature = $event"
      @update:systemPrompt="aiConfigForm.system_prompt = $event"
      @update:isDefault="aiConfigForm.is_default = $event"
      @submit="saveAiConfig"
      @reset="resetAiForm"
    />

    <section class="sub-card">
      <div class="section-header compact">
        <h3>我的 AI 配置</h3>
        <span class="workspace-hint" v-if="loadingConfigs">加载中...</span>
      </div>

      <div v-if="systemDefault" class="default-card">
        <strong>系统默认配置</strong>
        <span>{{ systemDefault.provider }} / {{ systemDefault.model_name }} / 温度 {{ systemDefault.temperature }}</span>
      </div>

      <div v-if="configs.length === 0" class="empty-state">
        还没有个人 AI 配置，先创建一个吧。
      </div>

      <div v-else class="config-list">
        <article v-for="config in configs" :key="config.id" class="config-item">
          <div class="config-item-main">
            <div class="config-item-title">
              <strong>{{ config.provider }} / {{ config.model_name }}</strong>
              <span v-if="config.is_default" class="role-badge">默认</span>
            </div>
            <p>
              接口地址：{{ config.base_url || '未填写' }}
              <br />
              温度：{{ config.temperature }}
              <br />
              系统提示词：{{ config.system_prompt || '未填写' }}
            </p>
          </div>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="startEditConfig(config)">编辑</button>
            <button class="ghost-button" :disabled="deletingConfigId === config.id" type="button" @click="removeAiConfig(config.id)">
              {{ deletingConfigId === config.id ? '删除中...' : '删除' }}
            </button>
            <button class="ghost-button" type="button" @click="makeDefaultAiConfig(config.id)">设默认</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
