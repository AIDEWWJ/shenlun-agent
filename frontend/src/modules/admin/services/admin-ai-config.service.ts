import { request } from '@/shared/api/http'
import type {
  AiConfigCreatePayload,
  AiConfigRead,
  AiConfigUpdatePayload,
} from '@/modules/ai-config/types/ai-config'

export function listAdminSystemAiConfigs(token: string) {
  return request<AiConfigRead[]>('/admin/ai-configs/system', {
    token,
  })
}

export function createAdminSystemAiConfig(token: string, payload: AiConfigCreatePayload) {
  return request<AiConfigRead>('/admin/ai-configs/system', {
    method: 'POST',
    token,
    body: {
      ...payload,
      scope: 'system',
    },
  })
}

export function updateAdminSystemAiConfig(token: string, configId: number, payload: AiConfigUpdatePayload) {
  return request<AiConfigRead>(`/admin/ai-configs/system/${configId}`, {
    method: 'PUT',
    token,
    body: {
      ...payload,
      scope: 'system',
    },
  })
}

export function deleteAdminSystemAiConfig(token: string, configId: number) {
  return request<void>(`/admin/ai-configs/system/${configId}`, {
    method: 'DELETE',
    token,
  })
}

export function setAdminSystemDefaultAiConfig(token: string, configId: number) {
  return request<AiConfigRead>(`/admin/ai-configs/system/${configId}/default`, {
    method: 'POST',
    token,
  })
}
