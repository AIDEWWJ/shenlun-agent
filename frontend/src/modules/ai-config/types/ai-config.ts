export type AiProvider = 'openai-compatible' | 'openai' | 'deepseek' | 'openrouter' | 'custom'

export type AiConfigRead = {
  id: number
  user_id: number | null
  scope: string
  created_by: number | null
  provider: string
  model_name: string
  base_url: string | null
  temperature: number
  system_prompt: string | null
  is_default: boolean
  created_at: string
}

export type AiConfigCreatePayload = {
  provider: string
  model_name: string
  api_key: string
  base_url?: string | null
  temperature?: number
  system_prompt?: string | null
  is_default?: boolean
}

export type AiConfigUpdatePayload = Partial<AiConfigCreatePayload>
