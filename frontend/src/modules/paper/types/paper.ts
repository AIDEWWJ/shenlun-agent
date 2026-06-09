export interface Paper {
  id: number
  title: string
  category: string | null
  region: string | null
  difficulty: string | null
  year: number | null
  source_url: string | null
  scope: string
  question_count: number
  created_at: string
}

export interface PaperMaterial {
  id: number
  material_num: number
  content: string
  sort_order: number | null
}

export interface PaperQuestion {
  id: number
  material_refs: string | null
  requirement: string | null
  reference_answer: string | null
  difficulty: string | null
  sort_order: number | null
  question_type: string | null
}

export interface PaperDetail extends Paper {
  materials: PaperMaterial[]
  questions: PaperQuestion[]
}

export interface PaperListResponse {
  items: Paper[]
  total: number
  page: number
  page_size: number
}
