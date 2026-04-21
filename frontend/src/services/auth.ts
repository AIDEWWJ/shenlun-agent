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
  password: string
  email: string
}

export type RegisterConfirmPayload = {
  username: string
  email: string
  password: string
  verification_code: string
}

export type RegisterCodePayload = {
  username: string
  email: string
}

export type ProfileUpdatePayload = {
  username?: string | null
  email?: string | null
}

export type PasswordChangePayload = {
  current_password: string
  new_password: string
}

export type PasswordResetPayload = {
  username: string
  email: string
  new_password: string
}

export type PasswordResetConfirmPayload = PasswordResetPayload & {
  verification_code: string
}

export type PasswordResetCodePayload = {
  username: string
  email: string
}

type TokenResponse = {
  access_token: string
  token_type: string
}

export function sendRegisterVerificationCode(payload: RegisterCodePayload) {
  return request<void>('/auth/register/send-code', {
    method: 'POST',
    body: payload,
  })
}

export function registerUser(payload: RegisterConfirmPayload) {
  return request<TokenResponse>('/auth/register', {
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

export function updateCurrentUser(token: string, payload: ProfileUpdatePayload) {
  return request<UserRead>('/auth/me', {
    method: 'PUT',
    token,
    body: payload,
  })
}

export function changeCurrentUserPassword(token: string, payload: PasswordChangePayload) {
  return request<void>('/auth/me/password', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function sendForgotPasswordVerificationCode(payload: PasswordResetCodePayload) {
  return request<void>('/auth/forgot-password/send-code', {
    method: 'POST',
    body: payload,
  })
}

export function resetForgottenPassword(payload: PasswordResetConfirmPayload) {
  return request<void>('/auth/forgot-password', {
    method: 'POST',
    body: payload,
  })
}
