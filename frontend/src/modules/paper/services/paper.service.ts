import { request } from '@/shared/api/http'
import type { PaperDetail, PaperListResponse } from '../types/paper'

export async function listPapers(
  token: string,
  params: {
    page?: number
    page_size?: number
    keyword?: string
    region?: string
    difficulty?: string
    year?: number
    scope?: string
    sort_by?: string
    sort_order?: string
  } = {},
): Promise<PaperListResponse> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.set('page', String(params.page))
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  if (params.keyword) searchParams.set('keyword', params.keyword)
  if (params.region) searchParams.set('region', params.region)
  if (params.difficulty) searchParams.set('difficulty', params.difficulty)
  if (params.year) searchParams.set('year', String(params.year))
  if (params.scope) searchParams.set('scope', params.scope)
  if (params.sort_by) searchParams.set('sort_by', params.sort_by)
  if (params.sort_order) searchParams.set('sort_order', params.sort_order)

  const qs = searchParams.toString()
  const url = `/papers${qs ? `?${qs}` : ''}`
  return request<PaperListResponse>(url, { token })
}

export async function getPaperFilters(
  token: string,
  scope?: string,
): Promise<{ regions: string[]; years: number[]; difficulties: string[] }> {
  const qs = scope ? `?scope=${scope}` : ''
  return request(`/papers/filters${qs}`, { token })
}

export async function getPaperDetail(token: string, paperId: number): Promise<PaperDetail> {
  return request<PaperDetail>(`/papers/${paperId}`, { token })
}

export async function importPaper(token: string, data: Record<string, unknown>): Promise<{ paper: { id: number }; questions_created: number }> {
  return request('/papers/import', {
    method: 'POST',
    token,
    body: data,
  })
}

export async function deletePaper(token: string, paperId: number): Promise<void> {
  return request(`/papers/${paperId}`, {
    method: 'DELETE',
    token,
  })
}
