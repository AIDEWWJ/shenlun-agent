import { ref } from 'vue'

export type ReviewTab = 'summary' | 'paragraphs' | 'rewrite' | 'qa'

export function useReviewTabs(initialTab: ReviewTab = 'summary') {
  const activeTab = ref<ReviewTab>(initialTab)

  function setActiveTab(nextTab: ReviewTab) {
    activeTab.value = nextTab
  }

  return {
    activeTab,
    setActiveTab,
  }
}
