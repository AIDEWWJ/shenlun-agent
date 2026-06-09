import { request } from '@/shared/api/http'

// GET /api/practice-records - List practice records with filters
export async function listPracticeRecords(token: string, params?: {
  page?: number
  page_size?: number
  question_id?: number
  question_type?: string
  status?: string
  score_min?: number
  score_max?: number
  is_favorite?: boolean
  date_from?: string
  date_to?: string
}) {
  const searchParams = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.set(key, String(value))
      }
    })
  }
  const qs = searchParams.toString()
  return request<any>(`/practice-records${qs ? '?' + qs : ''}`, { token })
}

// GET /api/practice-records/{record_id} - Get record detail
export async function getPracticeRecord(token: string, recordId: number) {
  return request<any>(`/practice-records/${recordId}`, { token })
}

// PATCH /api/practice-records/{record_id}/favorite - Toggle favorite
export async function toggleFavorite(token: string, recordId: number, isFavorite: boolean) {
  return request<any>(`/practice-records/${recordId}/favorite`, { token, method: 'PATCH', body: { is_favorite: isFavorite } })
}
