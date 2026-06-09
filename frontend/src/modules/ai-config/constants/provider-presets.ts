import type { AiProvider } from '../types/ai-config'

export const providerPresets: Array<{
  provider: AiProvider
  label: string
  baseUrl: string
  model: string
  description: string
}> = [
  {
    provider: 'openai-compatible',
    label: 'OpenAI Compatible',
    baseUrl: 'https://api.example.com/v1',
    model: 'gpt-4.1-mini',
    description: '适合已经接入兼容 OpenAI 协议的第三方服务。',
  },
  {
    provider: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4.1-mini',
    description: '标准 OpenAI 接口，适合作为默认示例。',
  },
  {
    provider: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    description: '常见的中文写作场景配置示例。',
  },
  {
    provider: 'openrouter',
    label: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    model: 'openai/gpt-4o-mini',
    description: '适合需要频繁切换模型供应商的场景。',
  },
  {
    provider: 'custom',
    label: '自定义',
    baseUrl: '',
    model: '',
    description: '完全自定义 Base URL、模型名和系统提示词。',
  },
]

export const quickNotes = [
  'AI 批改结果仅用于训练参考，不等同于正式阅卷。',
  '浏览器端保存的 API Key 仅用于当前设备，不建议直接放生产秘钥。',
  '个人默认配置会被练习与报告页面优先读取，系统默认配置作为兜底。',
] as const
