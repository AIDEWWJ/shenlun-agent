import { request } from '@/shared/api/http'

// GET /api/error-notebook - List error notebook entries
export async function listErrorNotebook(token: string) {
  return request<any>('/error-notebook', { token })
}

// POST /api/error-notebook/generate - Generate error notebook from recent reviews
export async function generateErrorNotebook(token: string) {
  return request<any>('/error-notebook/generate', { token, method: 'POST', body: {} })
}

// PATCH /api/error-notebook/{entry_id}/resolve - Mark entry as resolved
export async function resolveEntry(token: string, entryId: number) {
  return request<any>(`/error-notebook/${entryId}/resolve`, { token, method: 'PATCH', body: {} })
}
