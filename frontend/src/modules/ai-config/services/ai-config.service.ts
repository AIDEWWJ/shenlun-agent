import { request } from '@/shared/api/http'

import type { AiConfigCreatePayload, AiConfigRead, AiConfigUpdatePayload } from '../types/ai-config'

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
