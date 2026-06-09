import { request } from '@/shared/api/http'

// GET /api/study-plans/me - Get user's study plan
export async function getStudyPlan(token: string) {
  return request<any>('/study-plans/me', { token })
}

// POST /api/study-plans/generate - Generate a new study plan
export async function generateStudyPlan(token: string) {
  return request<any>('/study-plans/generate', { token, method: 'POST', body: {} })
}
