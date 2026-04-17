import { request } from './api'

export type UserRead = {
  id: number
  username: string
  email: string | null
  status: string
  created_at: string
  roles: string[]
}

export type LoginPayload = {
  username: string
  password: string
}

export type RegisterPayload = {
  username: string
  email?: string | null
  password: string
}

type TokenResponse = {
  access_token: string
  token_type: string
}

export function registerUser(payload: RegisterPayload) {
  return request<UserRead>('/auth/register', {
    method: 'POST',
    body: payload,
  })
}

export function loginUser(payload: LoginPayload) {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: payload,
  })
}

export function fetchCurrentUser(token: string) {
  return request<UserRead>('/auth/me', {
    token,
  })
}
