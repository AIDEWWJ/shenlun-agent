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

export type TokenResponse = {
  access_token: string
  token_type: string
}
