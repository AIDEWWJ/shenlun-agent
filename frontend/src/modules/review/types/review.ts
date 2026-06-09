import type { QuestionType } from '@/modules/question/types/question'

export type ReportDimension = {
  name: string
  score: number
  maxScore: number
  comment: string
}

export type ParagraphReview = {
  id: string
  title: string
  excerpt: string
  issue: string
  suggestion: string
}

export type PracticeReportRecord = {
  id: string
  questionId: number
  questionTitle: string
  questionType: QuestionType
  source: string
  createdAt: string
  totalScore: number
  provider: string
  model: string
  overallComment: string
  strengths: string[]
  issues: string[]
  suggestions: string[]
  dimensions: ReportDimension[]
  paragraphReviews: ParagraphReview[]
  answers: Record<string, string>
  answerText: string
  referenceAnswer: string
  optimizedExample: string
}
