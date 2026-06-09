export type QuestionCategory = '真题' | '模拟题' | '专项训练'

export type QuestionType = '概括题' | '对策题' | '公文题' | '大作文'

export type DifficultyLevel = '基础' | '进阶' | '冲刺'

export type MaterialSection = {
  id: string
  title: string
  summary: string
  content: string
}

export type AnswerSection = {
  id: string
  title: string
  prompt: string
  wordLimitLabel: string
  minWords: number
  placeholder: string
}

export type QuestionRecord = {
  id: number
  title: string
  category: QuestionCategory
  source: string
  year: number
  region: string
  questionType: QuestionType
  difficulty: DifficultyLevel
  theme: string
  materialCount: number
  suggestedMinutes: number
  aiSupported: boolean
  tags: string[]
  coverNote: string
  intro: string
  overview: string
  tasks: string[]
  instructions: string[]
  notices: string[]
  materials: MaterialSection[]
  answerSections: AnswerSection[]
  referenceAnswer: string
  optimizedExample: string
}
