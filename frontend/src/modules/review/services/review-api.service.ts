import { request } from '@/shared/api/http'

// GET /api/reviews - List user's review records
export async function listReviews(token: string, params?: { page?: number; page_size?: number; question_id?: number; question_type?: string }) {
  const searchParams = new URLSearchParams()
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.page_size) searchParams.set('page_size', String(params.page_size))
  if (params?.question_id) searchParams.set('question_id', String(params.question_id))
  if (params?.question_type) searchParams.set('question_type', params.question_type)
  const qs = searchParams.toString()
  return request<any>(`/reviews${qs ? '?' + qs : ''}`, { token })
}

// GET /api/reviews/{review_id} - Get review detail
export async function getReviewDetail(token: string, reviewId: number) {
  return request<any>(`/reviews/${reviewId}`, { token })
}

// POST /api/reviews/{review_id}/rerun - Re-run review with updated AI
export async function rerunReview(token: string, reviewId: number) {
  return request<any>(`/reviews/${reviewId}/rerun`, { token, method: 'POST', body: {} })
}

// GET /api/reviews/{review_id}/compare/{target_review_id} - Compare two reviews
export async function compareReviews(token: string, reviewId: number, targetReviewId: number) {
  return request<any>(`/reviews/${reviewId}/compare/${targetReviewId}`, { token })
}

// POST /api/reviews/{review_id}/qa - Ask a follow-up question about a review
export async function askReviewQuestion(token: string, reviewId: number, data: { question: string; conversation_id?: string }) {
  return request<any>(`/reviews/${reviewId}/qa`, { token, method: 'POST', body: data })
}

// GET /api/reviews/{review_id}/qa - List Q&A history for a review
export async function listReviewQA(token: string, reviewId: number, params?: { conversation_id?: string; page?: number; page_size?: number }) {
  const searchParams = new URLSearchParams()
  if (params?.conversation_id) searchParams.set('conversation_id', params.conversation_id)
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.page_size) searchParams.set('page_size', String(params.page_size))
  const qs = searchParams.toString()
  return request<any>(`/reviews/${reviewId}/qa${qs ? '?' + qs : ''}`, { token })
}

// POST /api/review - Submit review for an existing answer_id
export async function submitReview(token: string, data: { answer_id: number }) {
  return request<any>('/review', { token, method: 'POST', body: data })
}

// POST /api/review/from-content - Submit review from raw content
export async function submitReviewFromContent(token: string, data: { question_id: number; content: string }) {
  return request<any>('/review/from-content', { token, method: 'POST', body: data })
}

// POST /api/analyze - AI analyze question
export async function analyzeQuestion(token: string, data: { question_id: number }) {
  return request<any>('/analyze', { token, method: 'POST', body: data })
}

// POST /api/outline - AI generate outline
export async function generateOutline(token: string, data: { question_id: number }) {
  return request<any>('/outline', { token, method: 'POST', body: data })
}

// POST /api/answers/{answer_id}/duplicate - Duplicate an answer
export async function duplicateAnswer(token: string, answerId: number) {
  return request<any>(`/answers/${answerId}/duplicate`, { token, method: 'POST', body: {} })
}
