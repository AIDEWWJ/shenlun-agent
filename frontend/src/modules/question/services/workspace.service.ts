import { request } from '@/shared/api/http'

// GET /api/questions/{question_id}/workspace - Get workspace data for practice
export async function getWorkspace(token: string, questionId: number) {
  return request<any>(`/questions/${questionId}/workspace`, { token })
}

// GET /api/questions/{question_id}/latest-answer - Get latest answer for a question
export async function getLatestAnswer(token: string, questionId: number) {
  return request<any>(`/questions/${questionId}/latest-answer`, { token })
}

// GET /api/questions/favorites - List user's favorite questions
export async function listFavoriteQuestions(token: string) {
  return request<any>('/questions/favorites', { token })
}

// POST /api/questions/{question_id}/favorite - Toggle question favorite
export async function toggleQuestionFavorite(token: string, questionId: number) {
  return request<any>(`/questions/${questionId}/favorite`, { token, method: 'POST', body: {} })
}

// POST /api/questions - Create question
export async function createQuestion(token: string, data: any) {
  return request<any>('/questions', { token, method: 'POST', body: data })
}

// PUT /api/questions/{question_id} - Update question
export async function updateQuestion(token: string, questionId: number, data: any) {
  return request<any>(`/questions/${questionId}`, { token, method: 'PUT', body: data })
}

// DELETE /api/questions/{question_id} - Delete question
export async function deleteQuestion(token: string, questionId: number) {
  return request<any>(`/questions/${questionId}`, { token, method: 'DELETE' })
}

// POST /api/questions/import - Batch import questions
export async function importQuestions(token: string, data: { questions: any[] }) {
  return request<any>('/questions/import', { token, method: 'POST', body: data })
}

// GET /api/questions/random - Get a random question
export async function getRandomQuestion(token?: string) {
  return request<any>('/questions/random', { token })
}
