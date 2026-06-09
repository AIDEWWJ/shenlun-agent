import { computed, reactive, ref, watch, type Ref } from 'vue'

import type { QuestionRecord } from '@/modules/question/types/question'
import type { PracticeDraft } from '../types/practice'

function createEmptyAnswers(question: QuestionRecord | null) {
  const entries = question?.answerSections.map((section) => [section.id, '']) ?? []
  return Object.fromEntries(entries)
}

export function readStoredPracticeDraft(questionId: number): PracticeDraft | null {
  try {
    const raw = localStorage.getItem(`shenlun-practice-draft:${questionId}`)
    if (!raw) {
      return null
    }
    return JSON.parse(raw) as PracticeDraft
  } catch {
    return null
  }
}

export function usePracticeDraft(question: Ref<QuestionRecord | null>) {
  const answers = reactive<Record<string, string>>({})
  const updatedAt = ref('')

  function hydrate(nextQuestion: QuestionRecord | null) {
    const nextAnswers = createEmptyAnswers(nextQuestion)
    Object.keys(answers).forEach((key) => {
      delete answers[key]
    })

    if (!nextQuestion) {
      updatedAt.value = ''
      return
    }

    const storedDraft = readStoredPracticeDraft(nextQuestion.id)
    const draftAnswers = storedDraft?.answers ?? nextAnswers

    Object.entries({ ...nextAnswers, ...draftAnswers }).forEach(([key, value]) => {
      answers[key] = value
    })

    updatedAt.value = storedDraft?.updatedAt ?? ''
  }

  function persist() {
    if (!question.value) {
      return
    }

    const payload: PracticeDraft = {
      questionId: question.value.id,
      answers: { ...answers },
      updatedAt: new Date().toISOString(),
    }

    updatedAt.value = payload.updatedAt

    try {
      localStorage.setItem(`shenlun-practice-draft:${question.value.id}`, JSON.stringify(payload))
    } catch {
      // Ignore storage errors.
    }
  }

  function resetDraft() {
    hydrate(question.value)
    if (!question.value) {
      return
    }

    Object.keys(answers).forEach((key) => {
      answers[key] = ''
    })
    persist()
  }

  watch(question, hydrate, { immediate: true })
  watch(answers, persist, { deep: true })

  const totalWords = computed(() => Object.values(answers).join('').replace(/\s+/g, '').length)

  return {
    answers,
    updatedAt,
    totalWords,
    resetDraft,
  }
}
