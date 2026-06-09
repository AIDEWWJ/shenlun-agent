<script setup lang="ts">
defineProps<{
  title: string
  provider: string
  modelName: string
  apiKey: string
  baseUrl: string
  temperature: number
  systemPrompt: string
  isDefault: boolean
  saving: boolean
  submitLabel: string
  resetLabel: string
  allowDefault?: boolean
}>()

const emit = defineEmits<{
  'update:provider': [value: string]
  'update:modelName': [value: string]
  'update:apiKey': [value: string]
  'update:baseUrl': [value: string]
  'update:temperature': [value: number]
  'update:systemPrompt': [value: string]
  'update:isDefault': [value: boolean]
  submit: []
  reset: []
}>()

function updateProvider(event: Event) {
  emit('update:provider', (event.target as HTMLInputElement).value)
}

function updateModelName(event: Event) {
  emit('update:modelName', (event.target as HTMLInputElement).value)
}

function updateApiKey(event: Event) {
  emit('update:apiKey', (event.target as HTMLInputElement).value)
}

function updateBaseUrl(event: Event) {
  emit('update:baseUrl', (event.target as HTMLInputElement).value)
}

function updateTemperature(event: Event) {
  emit('update:temperature', Number((event.target as HTMLInputElement).value))
}

function updateSystemPrompt(event: Event) {
  emit('update:systemPrompt', (event.target as HTMLTextAreaElement).value)
}

function updateIsDefault(event: Event) {
  emit('update:isDefault', (event.target as HTMLInputElement).checked)
}
</script>

<template>
  <section class="sub-card admin-form-card">
    <div class="section-header compact">
      <div>
        <p class="panel-kicker">AI 配置</p>
        <h3>{{ title }}</h3>
      </div>
      <button class="ghost-button" type="button" @click="$emit('reset')">{{ resetLabel }}</button>
    </div>

    <div class="form-grid config-form">
      <div class="field">
        <label>服务商</label>
        <input :value="provider" placeholder="openai" @input="updateProvider" />
      </div>
      <div class="field">
        <label>模型名</label>
        <input :value="modelName" placeholder="gpt-4.1-mini" @input="updateModelName" />
      </div>
      <div class="field">
        <label>API Key</label>
        <input :value="apiKey" placeholder="sk-..." type="password" @input="updateApiKey" />
      </div>
      <div class="field">
        <label>接口地址</label>
        <input :value="baseUrl" placeholder="https://api.openai.com/v1" @input="updateBaseUrl" />
      </div>
      <div class="field">
        <label>温度</label>
        <input :value="temperature" max="2" min="0" step="0.1" type="number" @input="updateTemperature" />
      </div>
      <div class="field field-wide">
        <label>系统提示词</label>
        <textarea :value="systemPrompt" rows="4" placeholder="可选，用于覆盖默认系统提示词" @input="updateSystemPrompt"></textarea>
      </div>
      <label v-if="allowDefault !== false" class="checkbox-row">
        <input :checked="isDefault" type="checkbox" @change="updateIsDefault" />
        设为默认配置
      </label>
    </div>

    <button class="primary-button" :disabled="saving" type="button" @click="$emit('submit')">
      {{ saving ? '保存中...' : submitLabel }}
    </button>
  </section>
</template>
