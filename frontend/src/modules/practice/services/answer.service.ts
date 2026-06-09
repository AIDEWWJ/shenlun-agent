import { request } from '@/shared/api/http'

// POST /api/answers - Create a new answer version
export async function createAnswer(token: string, data: { question_id: number; content: string }) {
  return request<any>('/answers', { token, method: 'POST', body: data })
}

// GET /api/questions/{question_id}/answers - List answer versions for a question
export async function listAnswers(token: string, questionId: number, page = 1, pageSize = 20) {
  return request<any>(`/questions/${questionId}/answers?page=${page}&page_size=${pageSize}`, { token })
}

// GET /api/answers/{answer_id} - Get answer detail
export async function getAnswer(token: string, answerId: number) {
  return request<any>(`/answers/${answerId}`, { token })
}

// PUT /api/answers/{answer_id} - Update an answer (only if not yet reviewed)
export async function updateAnswer(token: string, answerId: number, data: { content: string }) {
  return request<any>(`/answers/${answerId}`, { token, method: 'PUT', body: data })
}
