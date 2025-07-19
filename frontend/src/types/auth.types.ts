import type { User, Session } from '@supabase/supabase-js'

// Authentication types
export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
  fullName: string
  acceptTerms: boolean
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  password: string
  confirmPassword: string
}

export interface ChangePasswordRequest {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

export interface AuthResponse {
  success: boolean
  user?: User
  session?: Session
  error?: string
}

// User profile types
export interface UserProfile {
  id: string
  email: string
  full_name: string
  avatar_url?: string
  subscription_tier: SubscriptionTier
  created_at: string
  updated_at?: string
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone: string
  notifications: NotificationSettings
  privacy: PrivacySettings
}

export interface NotificationSettings {
  email_notifications: boolean
  push_notifications: boolean
  analysis_complete: boolean
  weekly_reports: boolean
  marketing_emails: boolean
}

export interface PrivacySettings {
  profile_visibility: 'private' | 'public'
  data_sharing: boolean
  analytics_tracking: boolean
}

// Subscription types
export type SubscriptionTier = 'free' | 'pro' | 'business' | 'enterprise'

export interface Subscription {
  id: string
  user_id: string
  tier: SubscriptionTier
  status: 'active' | 'canceled' | 'past_due' | 'unpaid'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  created_at: string
  updated_at: string
}

export interface SubscriptionFeatures {
  max_analyses_per_month: number
  max_concurrent_analyses: number
  historical_data_retention_days: number
  api_access: boolean
  priority_support: boolean
  white_label: boolean
  custom_reports: boolean
  team_collaboration: boolean
}

// Usage statistics
export interface UsageStats {
  current_month: {
    analyses_count: number
    analyses_limit: number
    storage_used_mb: number
    storage_limit_mb: number
  }
  all_time: {
    total_analyses: number
    total_reports_generated: number
    account_created: string
    last_activity: string
  }
}

// Authentication state
export interface AuthState {
  user: User | null
  profile: UserProfile | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  accessToken: string | null
  refreshToken: string | null
  isInitialized: boolean
}

// Form validation types
export interface ValidationError {
  field: string
  message: string
}

export interface FormState {
  isValid: boolean
  errors: ValidationError[]
  touched: Record<string, boolean>
}

// Password strength
export interface PasswordStrength {
  score: number // 0-4
  feedback: string[]
  suggestions: string[]
  warning: string
}

// Social login providers
export type SocialProvider = 'google' | 'github' | 'twitter' | 'facebook' | 'linkedin'

export interface SocialLoginOptions {
  provider: SocialProvider
  redirectTo?: string
  scopes?: string
}

// Two-factor authentication
export interface TwoFactorAuth {
  enabled: boolean
  backup_codes: string[]
  qr_code?: string
  secret?: string
}

export interface TwoFactorSetupRequest {
  password: string
}

export interface TwoFactorVerifyRequest {
  token: string
  code: string
}

export interface TwoFactorDisableRequest {
  password: string
  code: string
}

// Session management
export interface SessionInfo {
  id: string
  user_agent: string
  ip_address: string
  location: string
  is_current: boolean
  last_activity: string
  created_at: string
}

// Account management
export interface AccountDeletionRequest {
  password: string
  reason?: string
  feedback?: string
}

export interface EmailChangeRequest {
  newEmail: string
  password: string
}

export interface EmailVerificationRequest {
  token: string
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// Error types
export interface AuthError {
  code: string
  message: string
  details?: any
}

export interface ValidationErrors {
  [key: string]: string[]
}

// Utility types
export type AuthEventType = 
  | 'SIGNED_IN'
  | 'SIGNED_OUT'
  | 'TOKEN_REFRESHED'
  | 'USER_UPDATED'
  | 'PASSWORD_RECOVERY'

export interface AuthEvent {
  type: AuthEventType
  session: Session | null
  user: User | null
}