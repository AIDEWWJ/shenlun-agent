import { request } from '@/shared/api/http'

// GET /api/dashboard/me - User dashboard data
export async function getDashboard(token: string) {
  return request<any>('/dashboard/me', { token })
}

// GET /api/stats/by-question-type - Stats grouped by question type
export async function getStatsByType(token: string) {
  return request<any>('/stats/by-question-type', { token })
}

// GET /api/stats/trend - Practice trend over time
export async function getStatsTrend(token: string) {
  return request<any>('/stats/trend', { token })
}

// GET /api/questions/random - Get a random question
export async function getRandomQuestion(token?: string) {
  return request<any>('/questions/random', { token })
}

// GET /api/questions/recommendations - Get recommended questions
export async function getRecommendations(token?: string) {
  return request<any>('/questions/recommendations', { token })
}
