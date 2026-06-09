export const i18nConfig = {
  defaultLocale: 'zh-CN',
  fallbackLocale: 'en-US',
  namespaces: ['common', 'question', 'practice', 'review', 'admin'],
} as const

export type Locale = (typeof i18nConfig)['defaultLocale'] | (typeof i18nConfig)['fallbackLocale']

export function t(message: string) {
  return message
}
