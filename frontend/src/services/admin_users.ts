import { request } from './api'
import type { UserRead } from './auth'

export type AdminUserCreatePayload = {
  username: string
  password: string
  email?: string | null
  status?: string
  roles?: string[]
}

export type AdminUserUpdatePayload = {
  username?: string | null
  password?: string | null
  email?: string | null
  status?: string | null
  roles?: string[] | null
}

export function listAdminUsers(token: string) {
  return request<UserRead[]>('/admin/users', {
    token,
  })
}

export function fetchAdminUser(token: string, userId: number) {
  return request<UserRead>(`/admin/users/${userId}`, {
    token,
  })
}

export function createAdminUser(token: string, payload: AdminUserCreatePayload) {
  return request<UserRead>('/admin/users', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function updateAdminUser(token: string, userId: number, payload: AdminUserUpdatePayload) {
  return request<UserRead>(`/admin/users/${userId}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}

export function deleteAdminUser(token: string, userId: number) {
  return request<void>(`/admin/users/${userId}`, {
    method: 'DELETE',
    token,
  })
}
