export type LibraryItemType = 'paper' | 'question'
export type LibraryItemTypeFilter = 'all' | LibraryItemType

export interface LibraryAction {
  label: string
  path: string
}

export interface LibraryItem {
  item_key: string
  item_type: LibraryItemType
  resource_id: number
  title: string
  source: string | null
  year: number | null
  region: string | null
  difficulty: string | null
  question_type: string | null
  question_count: number | null
  suggested_minutes: number | null
  scope: string
  tags: string[]
  has_draft: boolean
  created_at: string | null
  updated_at: string | null
  primary_action: LibraryAction
  secondary_action: LibraryAction | null
}

export interface LibraryItemListResponse {
  items: LibraryItem[]
  total: number
  page: number
  page_size: number
  applied_filters: Record<string, string | number | null>
  applied_sort: Record<string, string>
}

export interface LibraryFilterOptions {
  item_types: LibraryItemType[]
  scopes: string[]
  regions: string[]
  years: number[]
  difficulties: string[]
  question_types: string[]
  sort_fields: string[]
  default_sort_by: string
  default_sort_order: string
}

