import type { QuestionType } from '@/modules/question/types/question'

export type PracticeDraft = {
  questionId: number
  answers: Record<string, string>
  updatedAt: string
}

export type HistoryRecord =
  | {
      id: string
      kind: 'report'
      questionId: number
      questionTitle: string
      questionType: QuestionType
      source: string
      timestamp: string
      score: number
      status: '已批改'
      modelLabel: string
    }
  | {
      id: string
      kind: 'draft'
      questionId: number
      questionTitle: string
      questionType: QuestionType
      source: string
      timestamp: string
      score: null
      status: '草稿'
      modelLabel: string
    }
