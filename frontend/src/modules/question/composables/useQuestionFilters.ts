import { computed, ref } from 'vue'

import type { QuestionRecord } from '../types/question'

export function useQuestionFilters(questions: QuestionRecord[]) {
  const keyword = ref('')
  const category = ref('全部')

  const categories = computed(() => ['全部', ...new Set(questions.map((question) => question.category))])

  const filteredQuestions = computed(() => {
    const query = keyword.value.trim().toLowerCase()

    return questions.filter((question) => {
      const matchesCategory = category.value === '全部' || question.category === category.value
      const matchesKeyword =
        query.length === 0 ||
        [question.title, question.theme, question.source, ...question.tags]
          .join(' ')
          .toLowerCase()
          .includes(query)

      return matchesCategory && matchesKeyword
    })
  })

  return {
    keyword,
    category,
    categories,
    filteredQuestions,
  }
}
