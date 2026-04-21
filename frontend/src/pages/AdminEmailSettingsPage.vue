<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import {
  createAdminEmailConfig,
  createAdminEmailTemplate,
  deleteAdminEmailConfig,
  deleteAdminEmailTemplate,
  listAdminEmailConfigs,
  listAdminEmailTemplates,
  updateAdminEmailConfig,
  updateAdminEmailTemplate,
  type EmailConfigPayload,
  type EmailConfigRead,
  type EmailTemplatePayload,
  type EmailTemplateRead,
} from '../services/admin_emails'

const props = defineProps<{
  token: string | null
}>()

const configs = ref<EmailConfigRead[]>([])
const templates = ref<EmailTemplateRead[]>([])
const configLoading = ref(false)
const templateLoading = ref(false)
const savingConfig = ref(false)
const savingTemplate = ref(false)
const deletingConfigId = ref<number | null>(null)
const deletingTemplateKey = ref('')
const editingConfigId = ref<number | null>(null)
const editingTemplateKey = ref('')
const notice = ref('')
const error = ref('')

const configForm = reactive<EmailConfigPayload>({
  name: 'default',
  smtp_host: 'smtp.example.com',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  sender_email: 'noreply@example.com',
  sender_name: '申论 Agent',
  use_tls: true,
  use_ssl: false,
  enabled: true,
})

const templateForm = reactive<EmailTemplatePayload>({
  template_key: 'register_verify',
  template_name: '注册验证码',
  subject: '{app_name} 注册验证码',
  body_text: '您好，{username}。你的注册验证码是：{code}。有效期 {expires_minutes} 分钟。',
  body_html: '<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>',
  enabled: true,
})

const isEditingConfig = computed(() => editingConfigId.value !== null)
const isEditingTemplate = computed(() => editingTemplateKey.value !== '')

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

function resetConfigForm() {
  editingConfigId.value = null
  configForm.name = 'default'
  configForm.smtp_host = 'smtp.example.com'
  configForm.smtp_port = 587
  configForm.smtp_username = ''
  configForm.smtp_password = ''
  configForm.sender_email = 'noreply@example.com'
  configForm.sender_name = '申论 Agent'
  configForm.use_tls = true
  configForm.use_ssl = false
  configForm.enabled = true
}

function fillConfigForm(item: EmailConfigRead) {
  editingConfigId.value = item.id
  configForm.name = item.name
  configForm.smtp_host = item.smtp_host
  configForm.smtp_port = item.smtp_port
  configForm.smtp_username = item.smtp_username ?? ''
  configForm.smtp_password = ''
  configForm.sender_email = item.sender_email
  configForm.sender_name = item.sender_name ?? ''
  configForm.use_tls = item.use_tls
  configForm.use_ssl = item.use_ssl
  configForm.enabled = item.enabled
}

function resetTemplateForm() {
  editingTemplateKey.value = ''
  templateForm.template_key = 'register_verify'
  templateForm.template_name = '注册验证码'
  templateForm.subject = '{app_name} 注册验证码'
  templateForm.body_text = '您好，{username}。你的注册验证码是：{code}。有效期 {expires_minutes} 分钟。'
  templateForm.body_html = '<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>'
  templateForm.enabled = true
}

function fillTemplateForm(item: EmailTemplateRead) {
  editingTemplateKey.value = item.template_key
  templateForm.template_key = item.template_key
  templateForm.template_name = item.template_name
  templateForm.subject = item.subject
  templateForm.body_text = item.body_text
  templateForm.body_html = item.body_html ?? ''
  templateForm.enabled = item.enabled
}

async function loadConfigs() {
  if (!props.token) {
    configs.value = []
    return
  }

  configLoading.value = true
  try {
    configs.value = await listAdminEmailConfigs(props.token)
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载邮件配置失败')
  } finally {
    configLoading.value = false
  }
}

async function loadTemplates() {
  if (!props.token) {
    templates.value = []
    return
  }

  templateLoading.value = true
  try {
    templates.value = await listAdminEmailTemplates(props.token)
  } catch (err) {
    setError(err instanceof Error ? err.message : '加载邮件模板失败')
  } finally {
    templateLoading.value = false
  }
}

async function saveConfig() {
  if (!props.token) {
    return
  }

  savingConfig.value = true
  resetMessages()
  try {
    const payload: EmailConfigPayload = {
      ...configForm,
      smtp_username: configForm.smtp_username?.trim() || null,
      smtp_password: configForm.smtp_password?.trim() || null,
      sender_name: configForm.sender_name?.trim() || null,
    }

    if (editingConfigId.value === null) {
      await createAdminEmailConfig(props.token, payload)
      setNotice('已创建邮件配置')
    } else {
      await updateAdminEmailConfig(props.token, editingConfigId.value, payload)
      setNotice('已更新邮件配置')
    }

    resetConfigForm()
    await loadConfigs()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存邮件配置失败')
  } finally {
    savingConfig.value = false
  }
}

async function saveTemplate() {
  if (!props.token) {
    return
  }

  savingTemplate.value = true
  resetMessages()
  try {
    const payload: EmailTemplatePayload = {
      template_key: templateForm.template_key.trim(),
      template_name: templateForm.template_name.trim(),
      subject: templateForm.subject.trim(),
      body_text: templateForm.body_text.trim(),
      body_html: templateForm.body_html?.trim() || null,
      enabled: templateForm.enabled,
    }

    if (editingTemplateKey.value === '') {
      await createAdminEmailTemplate(props.token, payload)
      setNotice('已创建邮件模板')
    } else {
      await updateAdminEmailTemplate(props.token, editingTemplateKey.value, payload)
      setNotice('已更新邮件模板')
    }

    resetTemplateForm()
    await loadTemplates()
  } catch (err) {
    setError(err instanceof Error ? err.message : '保存邮件模板失败')
  } finally {
    savingTemplate.value = false
  }
}

async function removeConfig(configId: number) {
  if (!props.token) {
    return
  }

  deletingConfigId.value = configId
  resetMessages()
  try {
    await deleteAdminEmailConfig(props.token, configId)
    if (editingConfigId.value === configId) {
      resetConfigForm()
    }
    await loadConfigs()
    setNotice('已删除邮件配置')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除邮件配置失败')
  } finally {
    deletingConfigId.value = null
  }
}

async function removeTemplate(templateKey: string) {
  if (!props.token) {
    return
  }

  deletingTemplateKey.value = templateKey
  resetMessages()
  try {
    await deleteAdminEmailTemplate(props.token, templateKey)
    if (editingTemplateKey.value === templateKey) {
      resetTemplateForm()
    }
    await loadTemplates()
    setNotice('已删除邮件模板')
  } catch (err) {
    setError(err instanceof Error ? err.message : '删除邮件模板失败')
  } finally {
    deletingTemplateKey.value = ''
  }
}

watch(
  () => props.token,
  () => {
    resetMessages()
    resetConfigForm()
    resetTemplateForm()
    void loadConfigs()
    void loadTemplates()
  },
  { immediate: true },
)

onMounted(() => {
  void loadConfigs()
  void loadTemplates()
})
</script>

<script lang="ts">
export default {
  name: 'AdminEmailSettingsPage',
}
</script>

<template>
  <div class="page-card page-section">
    <div class="section-header">
      <div>
        <p class="panel-kicker">管理员后台</p>
        <h2>邮件发送配置与模板</h2>
      </div>
      <span class="workspace-hint">用于注册验证、找回密码和后续通知</span>
    </div>

    <div v-if="notice" class="notice-box is-success">{{ notice }}</div>
    <div v-if="error" class="notice-box is-error">{{ error }}</div>

    <section class="sub-card">
      <div class="section-header compact">
        <h3>{{ isEditingConfig ? '编辑邮件配置' : '创建邮件配置' }}</h3>
        <button class="ghost-button" type="button" @click="resetConfigForm">重置</button>
      </div>

      <div class="form-grid admin-form-grid">
        <div class="field">
          <label>配置名称</label>
          <input v-model.trim="configForm.name" placeholder="default" />
        </div>
        <div class="field">
          <label>SMTP 主机</label>
          <input v-model.trim="configForm.smtp_host" placeholder="smtp.example.com" />
        </div>
        <div class="field">
          <label>SMTP 端口</label>
          <input v-model.number="configForm.smtp_port" type="number" min="1" max="65535" />
        </div>
        <div class="field">
          <label>SMTP 用户名</label>
          <input v-model.trim="configForm.smtp_username" placeholder="可选" />
        </div>
        <div class="field">
          <label>SMTP 密码</label>
          <input v-model.trim="configForm.smtp_password" type="password" placeholder="可选" />
        </div>
        <div class="field">
          <label>发件邮箱</label>
          <input v-model.trim="configForm.sender_email" placeholder="noreply@example.com" />
        </div>
        <div class="field">
          <label>发件名称</label>
          <input v-model.trim="configForm.sender_name" placeholder="申论 Agent" />
        </div>
        <label class="checkbox-row">
          <input v-model="configForm.use_tls" type="checkbox" />
          启用 TLS
        </label>
        <label class="checkbox-row">
          <input v-model="configForm.use_ssl" type="checkbox" />
          启用 SSL
        </label>
        <label class="checkbox-row">
          <input v-model="configForm.enabled" type="checkbox" />
          启用配置
        </label>
      </div>

      <button class="primary-button" :disabled="savingConfig" type="button" @click="saveConfig">
        {{ savingConfig ? '保存中...' : isEditingConfig ? '更新邮件配置' : '创建邮件配置' }}
      </button>
    </section>

    <section class="sub-card">
      <div class="section-header compact">
        <h3>邮件配置列表</h3>
        <span class="workspace-hint" v-if="configLoading">加载中...</span>
      </div>

      <div v-if="configs.length === 0" class="empty-state">还没有邮件配置。</div>
      <div v-else class="config-list">
        <article v-for="item in configs" :key="item.id" class="config-item">
          <div class="config-item-main">
            <div class="config-item-title">
              <strong>{{ item.name }}</strong>
              <span v-if="item.enabled" class="role-badge">启用</span>
            </div>
            <p>
              {{ item.smtp_host }}:{{ item.smtp_port }}
              <br />
              发件邮箱：{{ item.sender_email }}
              <br />
              发件名称：{{ item.sender_name || '未填写' }}
            </p>
          </div>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="fillConfigForm(item)">编辑</button>
            <button class="ghost-button" :disabled="deletingConfigId === item.id" type="button" @click="removeConfig(item.id)">
              {{ deletingConfigId === item.id ? '删除中...' : '删除' }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="sub-card">
      <div class="section-header compact">
        <h3>{{ isEditingTemplate ? '编辑邮件模板' : '创建邮件模板' }}</h3>
        <button class="ghost-button" type="button" @click="resetTemplateForm">重置</button>
      </div>

      <div class="form-grid admin-form-grid">
        <div class="field">
          <label>模板键</label>
          <input v-model.trim="templateForm.template_key" placeholder="register_verify" :disabled="isEditingTemplate" />
        </div>
        <div class="field">
          <label>模板名称</label>
          <input v-model.trim="templateForm.template_name" placeholder="注册验证码" />
        </div>
        <div class="field field-wide">
          <label>邮件主题</label>
          <input v-model.trim="templateForm.subject" placeholder="{app_name} 注册验证码" />
        </div>
        <div class="field field-wide">
          <label>纯文本内容</label>
          <textarea v-model.trim="templateForm.body_text" rows="4" placeholder="邮件正文"></textarea>
        </div>
        <div class="field field-wide">
          <label>HTML 内容</label>
          <textarea v-model.trim="templateForm.body_html" rows="4" placeholder="可选 HTML 模板"></textarea>
        </div>
        <label class="checkbox-row">
          <input v-model="templateForm.enabled" type="checkbox" />
          启用模板
        </label>
      </div>

      <button class="primary-button" :disabled="savingTemplate" type="button" @click="saveTemplate">
        {{ savingTemplate ? '保存中...' : isEditingTemplate ? '更新邮件模板' : '创建邮件模板' }}
      </button>
    </section>

    <section class="sub-card">
      <div class="section-header compact">
        <h3>邮件模板列表</h3>
        <span class="workspace-hint" v-if="templateLoading">加载中...</span>
      </div>

      <div v-if="templates.length === 0" class="empty-state">还没有邮件模板。</div>
      <div v-else class="config-list">
        <article v-for="item in templates" :key="item.template_key" class="config-item">
          <div class="config-item-main">
            <div class="config-item-title">
              <strong>{{ item.template_name }}</strong>
              <span class="role-badge">{{ item.template_key }}</span>
            </div>
            <p>
              主题：{{ item.subject }}
              <br />
              正文：{{ item.body_text }}
            </p>
          </div>
          <div class="action-row">
            <button class="ghost-button" type="button" @click="fillTemplateForm(item)">编辑</button>
            <button class="ghost-button" :disabled="deletingTemplateKey === item.template_key" type="button" @click="removeTemplate(item.template_key)">
              {{ deletingTemplateKey === item.template_key ? '删除中...' : '删除' }}
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
