<script setup lang="ts">
import type { AiConfigRead } from '../services/ai_configs'

defineProps<{
  configs: AiConfigRead[]
  loading: boolean
  deletingConfigId: number | null
}>()

defineEmits<{
  edit: [config: AiConfigRead]
  delete: [configId: number]
  default: [configId: number]
}>()
</script>

<template>
  <div>
    <span v-if="loading" class="workspace-hint">加载中...</span>
    <div v-if="configs.length === 0" class="empty-state">还没有系统配置，先创建一个吧。</div>
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
          <button class="ghost-button" type="button" @click="$emit('edit', config)">编辑</button>
          <button class="ghost-button" :disabled="deletingConfigId === config.id" type="button" @click="$emit('delete', config.id)">
            {{ deletingConfigId === config.id ? '删除中...' : '删除' }}
          </button>
          <button class="ghost-button" type="button" @click="$emit('default', config.id)">设默认</button>
        </div>
      </article>
    </div>
  </div>
</template>
