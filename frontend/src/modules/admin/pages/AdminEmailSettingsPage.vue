<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import AppIcon from '@/shared/components/AppIcon.vue'
import NoticeBanner from '@/shared/components/NoticeBanner.vue'
import { authStore } from '@/modules/auth/store'
import {
  createAdminEmailConfig, createAdminEmailTemplate,
  deleteAdminEmailConfig, deleteAdminEmailTemplate,
  listAdminEmailConfigs, listAdminEmailTemplates,
  updateAdminEmailConfig, updateAdminEmailTemplate,
  type EmailConfigPayload, type EmailConfigRead,
  type EmailTemplatePayload, type EmailTemplateRead,
} from '../services/admin-email.service'

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
  name: 'default', smtp_host: 'smtp.example.com', smtp_port: 587,
  smtp_username: '', smtp_password: '', sender_email: 'noreply@example.com',
  sender_name: '申论 Agent', use_tls: true, use_ssl: false, enabled: true,
})

const templateForm = reactive<EmailTemplatePayload>({
  template_key: 'register_verify', template_name: '注册验证码',
  subject: '{app_name} 注册验证码',
  body_text: '您好，{username}。你的注册验证码是：{code}。有效期 {expires_minutes} 分钟。',
  body_html: '<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>',
  enabled: true,
})

const isEditingConfig = computed(() => editingConfigId.value !== null)
const isEditingTemplate = computed(() => editingTemplateKey.value !== '')

function resetMessages() { notice.value = ''; error.value = '' }
function setNotice(msg: string) { notice.value = msg; error.value = '' }
function setError(msg: string) { error.value = msg; notice.value = '' }

function resetConfigForm() {
  editingConfigId.value = null
  configForm.name = 'default'; configForm.smtp_host = 'smtp.example.com'
  configForm.smtp_port = 587; configForm.smtp_username = ''; configForm.smtp_password = ''
  configForm.sender_email = 'noreply@example.com'; configForm.sender_name = '申论 Agent'
  configForm.use_tls = true; configForm.use_ssl = false; configForm.enabled = true
}

function fillConfigForm(item: EmailConfigRead) {
  editingConfigId.value = item.id
  configForm.name = item.name; configForm.smtp_host = item.smtp_host
  configForm.smtp_port = item.smtp_port; configForm.smtp_username = item.smtp_username ?? ''
  configForm.smtp_password = ''; configForm.sender_email = item.sender_email
  configForm.sender_name = item.sender_name ?? ''; configForm.use_tls = item.use_tls
  configForm.use_ssl = item.use_ssl; configForm.enabled = item.enabled
}

function resetTemplateForm() {
  editingTemplateKey.value = ''
  templateForm.template_key = 'register_verify'; templateForm.template_name = '注册验证码'
  templateForm.subject = '{app_name} 注册验证码'
  templateForm.body_text = '您好，{username}。你的注册验证码是：{code}。有效期 {expires_minutes} 分钟。'
  templateForm.body_html = '<p>您好，{username}。</p><p>你的注册验证码是：<strong>{code}</strong></p><p>有效期 {expires_minutes} 分钟。</p>'
  templateForm.enabled = true
}

function fillTemplateForm(item: EmailTemplateRead) {
  editingTemplateKey.value = item.template_key
  templateForm.template_key = item.template_key; templateForm.template_name = item.template_name
  templateForm.subject = item.subject; templateForm.body_text = item.body_text
  templateForm.body_html = item.body_html ?? ''; templateForm.enabled = item.enabled
}

async function loadConfigs() {
  if (!authStore.token) return
  configLoading.value = true
  try { configs.value = await listAdminEmailConfigs(authStore.token) }
  catch (err) { setError(err instanceof Error ? err.message : '加载邮件配置失败') }
  finally { configLoading.value = false }
}

async function loadTemplates() {
  if (!authStore.token) return
  templateLoading.value = true
  try { templates.value = await listAdminEmailTemplates(authStore.token) }
  catch (err) { setError(err instanceof Error ? err.message : '加载邮件模板失败') }
  finally { templateLoading.value = false }
}

async function saveConfig() {
  if (!authStore.token) return
  savingConfig.value = true; resetMessages()
  try {
    const payload: EmailConfigPayload = { ...configForm, smtp_username: configForm.smtp_username?.trim() || null, smtp_password: configForm.smtp_password?.trim() || null, sender_name: configForm.sender_name?.trim() || null }
    if (editingConfigId.value === null) { await createAdminEmailConfig(authStore.token, payload); setNotice('已创建邮件配置') }
    else { await updateAdminEmailConfig(authStore.token, editingConfigId.value, payload); setNotice('已更新邮件配置') }
    resetConfigForm(); await loadConfigs()
  } catch (err) { setError(err instanceof Error ? err.message : '保存邮件配置失败') }
  finally { savingConfig.value = false }
}

async function saveTemplate() {
  if (!authStore.token) return
  savingTemplate.value = true; resetMessages()
  try {
    const payload: EmailTemplatePayload = { template_key: templateForm.template_key.trim(), template_name: templateForm.template_name.trim(), subject: templateForm.subject.trim(), body_text: templateForm.body_text.trim(), body_html: templateForm.body_html?.trim() || null, enabled: templateForm.enabled }
    if (editingTemplateKey.value === '') { await createAdminEmailTemplate(authStore.token, payload); setNotice('已创建邮件模板') }
    else { await updateAdminEmailTemplate(authStore.token, editingTemplateKey.value, payload); setNotice('已更新邮件模板') }
    resetTemplateForm(); await loadTemplates()
  } catch (err) { setError(err instanceof Error ? err.message : '保存邮件模板失败') }
  finally { savingTemplate.value = false }
}

async function removeConfig(configId: number) {
  if (!authStore.token) return
  deletingConfigId.value = configId; resetMessages()
  try { await deleteAdminEmailConfig(authStore.token, configId); if (editingConfigId.value === configId) resetConfigForm(); await loadConfigs(); setNotice('已删除邮件配置') }
  catch (err) { setError(err instanceof Error ? err.message : '删除邮件配置失败') }
  finally { deletingConfigId.value = null }
}

async function removeTemplate(templateKey: string) {
  if (!authStore.token) return
  deletingTemplateKey.value = templateKey; resetMessages()
  try { await deleteAdminEmailTemplate(authStore.token, templateKey); if (editingTemplateKey.value === templateKey) resetTemplateForm(); await loadTemplates(); setNotice('已删除邮件模板') }
  catch (err) { setError(err instanceof Error ? err.message : '删除邮件模板失败') }
  finally { deletingTemplateKey.value = '' }
}

onMounted(() => { void loadConfigs(); void loadTemplates() })
</script>

<template>
  <div class="page-content">
    <header class="page-header">
      <div>
        <h1>邮件配置</h1>
        <p>维护 SMTP、模板和通知链路</p>
      </div>
    </header>

    <NoticeBanner v-if="notice" :message="notice" tone="success" />
    <NoticeBanner v-if="error" :message="error" tone="error" />

    <!-- Email Config Section -->
    <section class="section">
      <div class="section-title">
        <div class="section-icon"><AppIcon name="info" :size="16" /></div>
        <div>
          <h2>邮件发送配置</h2>
          <p>用于系统发送通知邮件的 SMTP 服务配置</p>
        </div>
      </div>

      <div class="admin-grid">
        <div class="card">
          <div class="card-header">
            <h3>{{ isEditingConfig ? '编辑邮件配置' : '创建邮件配置' }}</h3>
            <button v-if="isEditingConfig" type="button" class="link-btn" @click="resetConfigForm">取消</button>
          </div>
          <div class="card-body">
            <div class="form-grid">
              <div class="field">
                <label>配置名称</label>
                <input v-model.trim="configForm.name" placeholder="default" />
              </div>
              <div class="field">
                <label>SMTP 主机</label>
                <input v-model.trim="configForm.smtp_host" placeholder="smtp.example.com" />
              </div>
              <div class="field-row">
                <div class="field">
                  <label>SMTP 端口</label>
                  <input v-model.number="configForm.smtp_port" type="number" min="1" max="65535" />
                </div>
                <div class="field">
                  <label>发件邮箱</label>
                  <input v-model.trim="configForm.sender_email" placeholder="noreply@example.com" />
                </div>
              </div>
              <div class="field-row">
                <div class="field">
                  <label>SMTP 用户名</label>
                  <input v-model.trim="configForm.smtp_username" placeholder="可选" />
                </div>
                <div class="field">
                  <label>SMTP 密码</label>
                  <input v-model.trim="configForm.smtp_password" type="password" placeholder="可选" />
                </div>
              </div>
              <div class="field">
                <label>发件名称</label>
                <input v-model.trim="configForm.sender_name" placeholder="申论 Agent" />
              </div>
              <div class="checkbox-row">
                <label><input v-model="configForm.use_tls" type="checkbox" /> 启用 TLS</label>
                <label><input v-model="configForm.use_ssl" type="checkbox" /> 启用 SSL</label>
                <label><input v-model="configForm.enabled" type="checkbox" /> 启用配置</label>
              </div>
            </div>
            <button class="primary-btn" :disabled="savingConfig" type="button" @click="saveConfig">
              {{ savingConfig ? '保存中...' : isEditingConfig ? '更新邮件配置' : '创建邮件配置' }}
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>配置列表</h3>
            <span v-if="configLoading" class="loading-text">加载中...</span>
          </div>
          <div class="card-body">
            <div v-if="configs.length === 0" class="empty-text">还没有邮件配置</div>
            <div v-else class="item-list">
              <article v-for="item in configs" :key="item.id" class="list-item">
                <div class="item-head">
                  <div class="item-title">
                    <strong>{{ item.name }}</strong>
                    <span v-if="item.enabled" class="tag-green">启用</span>
                  </div>
                  <div class="item-actions">
                    <button type="button" class="act-btn" @click="fillConfigForm(item)">编辑</button>
                    <button type="button" class="act-btn danger" :disabled="deletingConfigId === item.id" @click="removeConfig(item.id)">
                      {{ deletingConfigId === item.id ? '删除中...' : '删除' }}
                    </button>
                  </div>
                </div>
                <div class="item-meta">
                  <p><strong>SMTP:</strong> {{ item.smtp_host }}:{{ item.smtp_port }}</p>
                  <p><strong>发件:</strong> {{ item.sender_name || '未填写' }} &lt;{{ item.sender_email }}&gt;</p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Divider -->
    <div class="divider"></div>

    <!-- Email Templates Section -->
    <section class="section">
      <div class="section-title">
        <div class="section-icon accent"><AppIcon name="document" :size="16" /></div>
        <div>
          <h2>邮件外发模板</h2>
          <p>定义注册验证码、通知等邮件的正文格式</p>
        </div>
      </div>

      <div class="admin-grid">
        <div class="card">
          <div class="card-header">
            <h3>{{ isEditingTemplate ? '编辑邮件模板' : '创建邮件模板' }}</h3>
            <button v-if="isEditingTemplate" type="button" class="link-btn" @click="resetTemplateForm">取消</button>
          </div>
          <div class="card-body">
            <div class="form-grid">
              <div class="field-row">
                <div class="field">
                  <label>模板键</label>
                  <input v-model.trim="templateForm.template_key" placeholder="register_verify" :disabled="isEditingTemplate" />
                </div>
                <div class="field">
                  <label>模板名称</label>
                  <input v-model.trim="templateForm.template_name" placeholder="注册验证码" />
                </div>
              </div>
              <div class="field">
                <label>邮件主题</label>
                <input v-model.trim="templateForm.subject" placeholder="{app_name} 注册验证码" />
              </div>
              <div class="field">
                <label>纯文本内容</label>
                <textarea v-model.trim="templateForm.body_text" rows="3" placeholder="邮件正文"></textarea>
              </div>
              <div class="field">
                <label>HTML 内容</label>
                <textarea v-model.trim="templateForm.body_html" rows="3" placeholder="可选 HTML 模板" class="mono"></textarea>
              </div>
              <div class="checkbox-row">
                <label><input v-model="templateForm.enabled" type="checkbox" /> 启用模板</label>
              </div>
            </div>
            <button class="primary-btn" :disabled="savingTemplate" type="button" @click="saveTemplate">
              {{ savingTemplate ? '保存中...' : isEditingTemplate ? '更新模板' : '创建模板' }}
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h3>模板列表</h3>
            <span v-if="templateLoading" class="loading-text">加载中...</span>
          </div>
          <div class="card-body">
            <div v-if="templates.length === 0" class="empty-text">还没有邮件模板</div>
            <div v-else class="item-list">
              <article v-for="item in templates" :key="item.template_key" class="list-item">
                <div class="item-head">
                  <div class="item-title">
                    <strong>{{ item.template_name }}</strong>
                    <span class="tag-mono">{{ item.template_key }}</span>
                  </div>
                  <div class="item-actions">
                    <button type="button" class="act-btn" @click="fillTemplateForm(item)">编辑</button>
                    <button type="button" class="act-btn danger" :disabled="deletingTemplateKey === item.template_key" @click="removeTemplate(item.template_key)">
                      {{ deletingTemplateKey === item.template_key ? '删除中...' : '删除' }}
                    </button>
                  </div>
                </div>
                <div class="item-meta">
                  <p><strong>主题:</strong> {{ item.subject }}</p>
                  <p class="truncate"><strong>正文:</strong> {{ item.body_text }}</p>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-content {
  padding: 32px 40px 64px;
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header { padding-bottom: 20px; border-bottom: 1px solid var(--line); }
.page-header h1 { font-size: 24px; font-weight: 700; color: var(--ink); margin: 0 0 4px; }
.page-header p { font-size: 13px; color: var(--muted); margin: 0; }

.section { display: flex; flex-direction: column; gap: 16px; }
.section-title { display: flex; align-items: flex-start; gap: 12px; }
.section-icon { width: 36px; height: 36px; border-radius: 10px; background: var(--bg-soft); color: var(--muted); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.section-icon.accent { background: var(--accent-soft); color: var(--accent); }
.section-title h2 { font-size: 16px; font-weight: 600; color: var(--ink); margin: 0 0 2px; }
.section-title p { font-size: 12px; color: var(--muted); margin: 0; }
.divider { height: 1px; background: var(--line); margin: 8px 0; }

.admin-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.card { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xl); overflow: hidden; }
.card-header { padding: 16px 24px; border-bottom: 1px solid var(--line-soft); display: flex; align-items: center; justify-content: space-between; }
.card-header h3 { font-size: 14px; font-weight: 600; color: var(--ink); margin: 0; }
.card-body { padding: 24px; }

.form-grid { display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 12px; font-weight: 600; color: var(--ink); }
.field input, .field textarea { padding: 9px 13px; border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--paper); font-size: 13px; color: var(--ink); outline: none; transition: border-color var(--transition-fast); }
.field input:focus, .field textarea:focus { border-color: var(--accent); }
.field input:disabled { background: var(--bg-soft); color: var(--support); }
.field textarea.mono { font-family: var(--font-mono); font-size: 12px; }

.checkbox-row { display: flex; align-items: center; gap: 16px; }
.checkbox-row label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); cursor: pointer; }

.primary-btn { display: inline-flex; align-items: center; justify-content: center; padding: 9px 20px; background: var(--accent); color: #fff; border: none; border-radius: var(--radius-md); font-size: 13px; font-weight: 600; cursor: pointer; transition: background var(--transition-fast); }
.primary-btn:hover:not(:disabled) { background: var(--accent-deep); }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.link-btn { background: none; border: none; color: var(--muted); font-size: 12px; cursor: pointer; padding: 4px 8px; border-radius: var(--radius-md); transition: all var(--transition-fast); }
.link-btn:hover { color: var(--accent); background: var(--accent-soft); }

.loading-text { font-size: 12px; color: var(--support); }
.empty-text { font-size: 13px; color: var(--support); }

.item-list { display: flex; flex-direction: column; gap: 10px; }
.list-item { padding: 16px; border: 1px solid var(--line); border-radius: var(--radius-lg); transition: border-color var(--transition-fast); }
.list-item:hover { border-color: var(--line-strong); }
.item-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.item-title { display: flex; align-items: center; gap: 8px; }
.item-title strong { font-size: 14px; font-weight: 600; color: var(--ink); }
.item-actions { display: flex; gap: 6px; flex-shrink: 0; }

.tag-green { padding: 2px 8px; background: #dcfce7; color: #166534; font-size: 10px; font-weight: 600; border-radius: 100px; border: 1px solid #bbf7d0; }
.tag-mono { padding: 2px 8px; background: var(--bg-soft); color: var(--muted); font-size: 11px; font-family: var(--font-mono); border-radius: var(--radius-md); border: 1px solid var(--line); }

.item-meta { font-size: 12px; color: var(--muted); line-height: 1.6; }
.item-meta strong { color: var(--ink); font-weight: 600; }
.truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.act-btn { display: inline-flex; align-items: center; gap: 4px; padding: 5px 10px; border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--paper); color: var(--muted); font-size: 12px; font-weight: 500; cursor: pointer; transition: all var(--transition-fast); }
.act-btn:hover:not(:disabled) { color: var(--accent); border-color: var(--accent); }
.act-btn.danger:hover:not(:disabled) { color: var(--danger); border-color: var(--danger); }

@media (max-width: 900px) {
  .admin-grid { grid-template-columns: 1fr; }
  .field-row { grid-template-columns: 1fr; }
}
</style>
