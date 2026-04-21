import { request } from './api'

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

export function listMyAiConfigs(token: string) {
  return request<AiConfigRead[]>('/ai-configs/me', {
    token,
  })
}

export function createMyAiConfig(token: string, payload: AiConfigCreatePayload) {
  return request<AiConfigRead>('/ai-configs/me', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function updateMyAiConfig(token: string, configId: number, payload: AiConfigUpdatePayload) {
  return request<AiConfigRead>(`/ai-configs/me/${configId}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}

export function deleteMyAiConfig(token: string, configId: number) {
  return request<void>(`/ai-configs/me/${configId}`, {
    method: 'DELETE',
    token,
  })
}

export function setMyDefaultAiConfig(token: string, configId: number) {
  return request<AiConfigRead>(`/ai-configs/me/${configId}/default`, {
    method: 'POST',
    token,
  })
}

export function fetchSystemDefaultAiConfig() {
  return request<AiConfigRead | null>('/ai-configs/system-default')
}