import { request } from '@/shared/api/http'

export interface PaperSessionData {
  id: number
  paper_id: number
  answers: Record<number, string>
  current_index: number
  timer_seconds: number
  status: string
}

export async function getPaperSession(token: string, paperId: number): Promise<PaperSessionData | null> {
  return request(`/paper-sessions/${paperId}`, { token })
}

export async function savePaperSession(
  token: string,
  paperId: number,
  data: {
    answers: Record<number, string>
    current_index: number
    timer_seconds: number
    status?: string
  },
): Promise<{ id: number }> {
  return request(`/paper-sessions/${paperId}`, {
    method: 'POST',
    token,
    body: data,
  })
}

export async function deletePaperSession(token: string, paperId: number): Promise<void> {
  return request(`/paper-sessions/${paperId}`, {
    method: 'DELETE',
    token,
  })
}
