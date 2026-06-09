import { request } from '@/shared/api/http'

// GET /api/practice-sessions/current?question_id=X - Get current active session for a question
export async function getCurrentSession(token: string, questionId: number) {
  return request<any>(`/practice-sessions/current?question_id=${questionId}`, { token })
}

// POST /api/practice-sessions - Create a new practice session
export async function createSession(token: string, data: { question_id: number }) {
  return request<any>('/practice-sessions', { token, method: 'POST', body: data })
}

// PATCH /api/practice-sessions/{session_id} - Update session (e.g. status)
export async function updateSession(token: string, sessionId: number, data: any) {
  return request<any>(`/practice-sessions/${sessionId}`, { token, method: 'PATCH', body: data })
}

// POST /api/practice-sessions/{session_id}/submit - Submit session for AI review
export async function submitSession(token: string, sessionId: number, data?: any) {
  return request<any>(`/practice-sessions/${sessionId}/submit`, { token, method: 'POST', body: data || {} })
}
