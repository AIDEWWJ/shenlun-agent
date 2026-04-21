<script setup lang="ts">
import { computed, ref } from 'vue'

import { ApiError, request } from '../services/api'

const props = defineProps<{
  token: string | null
}>()

type PracticeAction = {
  endpoint: '/analyze' | '/outline' | '/review'
  label: string
  description: string
}

const actionBusy = ref(false)
const actionResult = ref('登录后点击任意按钮，就可以验证接口是否能正常返回结果。')
const feedback = ref('')

const practiceActions: PracticeAction[] = [
  {
    endpoint: '/analyze',
    label: '体验题目分析',
    description: '发起一次分析请求，查看返回是否正常。',
  },
  {
    endpoint: '/outline',
    label: '体验提纲生成',
    description: '发起一次提纲请求，确认流程是否可用。',
  },
  {
    endpoint: '/review',
    label: '体验批改接口',
    description: '发起一次批改请求，查看结果展示是否正常。',
  },
]

const tokenPreview = computed(() => {
  if (!props.token) {
    return '未登录'
  }

  return '已登录'
})

function setFeedback(message: string) {
  feedback.value = message
}

async function runProtectedAction(action: PracticeAction) {
  if (!props.token) {
    setFeedback('请先登录后再请求受保护接口。')
    return
  }

  feedback.value = ''
  actionBusy.value = true
  actionResult.value = `正在请求 ${action.endpoint} ...`

  try {
    const response = await request<Record<string, unknown>>(action.endpoint, {
      method: 'POST',
      token: props.token,
    })
    actionResult.value = JSON.stringify(response, null, 2)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      setFeedback('登录状态已失效，请重新登录。')
      actionResult.value = '401 未授权'
    } else if (error instanceof Error) {
      actionResult.value = error.message
    } else {
      actionResult.value = '请求失败，请稍后重试。'
    }
  } finally {
    actionBusy.value = false
  }
}
</script>

<script lang="ts">
export default {
  name: 'ApiDebugPanel',
}
</script>

<template>
  <div class="page-card page-section">
    <div class="section-header">
      <div>
        <p class="panel-kicker">接口联调</p>
        <h2>登录状态验证</h2>
      </div>
      <span class="workspace-hint">当前状态：{{ tokenPreview }}</span>
    </div>

    <p v-if="feedback" class="notice-box is-error">{{ feedback }}</p>

    <div class="action-list">
      <button
        v-for="action in practiceActions"
        :key="action.endpoint"
        class="action-card"
        :disabled="actionBusy"
        type="button"
        @click="runProtectedAction(action)"
      >
        <strong>{{ action.label }}</strong>
        <span>{{ action.description }}</span>
      </button>
    </div>

    <pre class="response-box">{{ actionResult }}</pre>
  </div>
</template>
