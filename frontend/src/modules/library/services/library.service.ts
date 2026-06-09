import { request } from '@/shared/api/http'
import type { LibraryFilterOptions, LibraryItemListResponse, LibraryItemTypeFilter } from '../types/library'

export async function listLibraryItems(
  token: string,
  params: {
    item_type?: LibraryItemTypeFilter
    page?: number
    page_size?: number
    keyword?: string
    region?: string
    difficulty?: string
    year?: number
    question_type?: string
    scope?: string
    sort_by?: string
    sort_order?: string
  } = {},
): Promise<LibraryItemListResponse> {
  const searchParams = new URLSearchParams()
  if (params.item_type) searchParams.set('item_type', params.item_type)
  if (params.page) searchParams.set('page', String(params.page))
  if (params.page_size) searchParams.set('page_size', String(params.page_size))
  if (params.keyword) searchParams.set('keyword', params.keyword)
  if (params.region) searchParams.set('region', params.region)
  if (params.difficulty) searchParams.set('difficulty', params.difficulty)
  if (params.year) searchParams.set('year', String(params.year))
  if (params.question_type) searchParams.set('question_type', params.question_type)
  if (params.scope) searchParams.set('scope', params.scope)
  if (params.sort_by) searchParams.set('sort_by', params.sort_by)
  if (params.sort_order) searchParams.set('sort_order', params.sort_order)

  const qs = searchParams.toString()
  return request<LibraryItemListResponse>(`/library/items${qs ? `?${qs}` : ''}`, { token })
}

export async function getLibraryFilters(token: string, scope?: string): Promise<LibraryFilterOptions> {
  const qs = scope ? `?scope=${scope}` : ''
  return request<LibraryFilterOptions>(`/library/filters${qs}`, { token })
}

