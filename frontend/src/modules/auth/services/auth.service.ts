import { request } from '@/shared/api/http'

import type {
  LoginPayload,
  PasswordChangePayload,
  PasswordResetCodePayload,
  PasswordResetConfirmPayload,
  ProfileUpdatePayload,
  RegisterCodePayload,
  RegisterConfirmPayload,
  TokenResponse,
  UserRead,
} from '../types/auth'

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
