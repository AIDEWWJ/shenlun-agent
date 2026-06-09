import { request } from '@/shared/api/http'

export type EmailConfigRead = {
  id: number
  name: string
  smtp_host: string
  smtp_port: number
  smtp_username: string | null
  sender_email: string
  sender_name: string | null
  use_tls: boolean
  use_ssl: boolean
  enabled: boolean
  created_at: string
  updated_at: string
}

export type EmailConfigPayload = {
  name: string
  smtp_host: string
  smtp_port: number
  smtp_username?: string | null
  smtp_password?: string | null
  sender_email: string
  sender_name?: string | null
  use_tls?: boolean
  use_ssl?: boolean
  enabled?: boolean
}

export type EmailTemplateRead = {
  id: number
  template_key: string
  template_name: string
  subject: string
  body_text: string
  body_html: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export type EmailTemplatePayload = {
  template_key: string
  template_name: string
  subject: string
  body_text: string
  body_html?: string | null
  enabled?: boolean
}

export function listAdminEmailConfigs(token: string) {
  return request<EmailConfigRead[]>('/admin/email/configs', {
    token,
  })
}

export function createAdminEmailConfig(token: string, payload: EmailConfigPayload) {
  return request<EmailConfigRead>('/admin/email/configs', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function updateAdminEmailConfig(token: string, configId: number, payload: EmailConfigPayload) {
  return request<EmailConfigRead>(`/admin/email/configs/${configId}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}

export function deleteAdminEmailConfig(token: string, configId: number) {
  return request<void>(`/admin/email/configs/${configId}`, {
    method: 'DELETE',
    token,
  })
}

export function listAdminEmailTemplates(token: string) {
  return request<EmailTemplateRead[]>('/admin/email/templates', {
    token,
  })
}

export function createAdminEmailTemplate(token: string, payload: EmailTemplatePayload) {
  return request<EmailTemplateRead>('/admin/email/templates', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function updateAdminEmailTemplate(token: string, templateKey: string, payload: Partial<EmailTemplatePayload>) {
  return request<EmailTemplateRead>(`/admin/email/templates/${templateKey}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}

export function deleteAdminEmailTemplate(token: string, templateKey: string) {
  return request<void>(`/admin/email/templates/${templateKey}`, {
    method: 'DELETE',
    token,
  })
}
