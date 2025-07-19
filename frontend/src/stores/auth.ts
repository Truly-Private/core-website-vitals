import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/services/supabase'
import { apiClient } from '@/services/api'
import type { User, AuthError } from '@supabase/supabase-js'
import type { 
  LoginCredentials, 
  RegisterCredentials, 
  UserProfile, 
  AuthResponse 
} from '@/types/auth.types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const profile = ref<UserProfile | null>(null)
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  
  // Getters
  const isAuthenticated = computed(() => !!user.value)
  const userEmail = computed(() => user.value?.email || '')
  const userName = computed(() => profile.value?.full_name || userEmail.value)
  const userAvatar = computed(() => profile.value?.avatar_url || '')
  const subscriptionTier = computed(() => profile.value?.subscription_tier || 'free')
  const hasActiveSubscription = computed(() => 
    subscriptionTier.value !== 'free' && subscriptionTier.value !== 'cancelled'
  )
  
  // Actions
  const initializeAuth = async () => {
    if (isInitialized.value) return
    
    isLoading.value = true
    error.value = null
    
    try {
      // Check if we have stored tokens (from localStorage via Pinia persist)
      if (accessToken.value && user.value) {
        // Verify the token is still valid by fetching the profile
        try {
          await fetchUserProfile()
        } catch (err) {
          // Token is invalid, clear auth state
          clearAuthState()
        }
      }
      
      isInitialized.value = true
    } catch (err) {
      console.error('Auth initialization error:', err)
      error.value = err instanceof Error ? err.message : 'Failed to initialize authentication'
    } finally {
      isLoading.value = false
    }
  }
  
  const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
    isLoading.value = true
    error.value = null
    
    try {
      // Use backend API for login instead of Supabase directly
      const response = await apiClient.post('/auth/login', {
        email: credentials.email,
        password: credentials.password,
      })
      
      if (response.data) {
        const { access_token, refresh_token: refresh_token_value, token_type, expires_in } = response.data
        
        // Store tokens
        accessToken.value = access_token
        refreshToken.value = refresh_token_value
        
        // Decode JWT to get user info
        const payload = JSON.parse(atob(access_token.split('.')[1]))
        user.value = {
          id: payload.sub,
          email: payload.email,
          user_metadata: {
            full_name: payload.full_name,
          },
        } as any
        
        // Fetch user profile to get complete data
        await fetchUserProfile()
        
        return {
          success: true,
          user: user.value,
          session: {
            access_token,
            refresh_token: refresh_token_value,
            token_type,
            expires_in,
          } as any,
        }
      }
      
      throw new Error('Login failed')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }
  
  const register = async (credentials: RegisterCredentials): Promise<AuthResponse> => {
    isLoading.value = true
    error.value = null
    
    try {
      // Use backend API for registration
      const response = await apiClient.post('/auth/register', {
        email: credentials.email,
        password: credentials.password,
        full_name: credentials.fullName,
      })
      
      if (response.data) {
        const { access_token, refresh_token: refresh_token_value, token_type, expires_in } = response.data
        
        // Store tokens
        accessToken.value = access_token
        refreshToken.value = refresh_token_value
        
        // Decode JWT to get user info
        const payload = JSON.parse(atob(access_token.split('.')[1]))
        user.value = {
          id: payload.sub,
          email: payload.email,
          user_metadata: {
            full_name: payload.full_name,
          },
        } as any
        
        // Fetch user profile to get complete data
        await fetchUserProfile()
        
        return {
          success: true,
          user: user.value,
          session: {
            access_token,
            refresh_token: refresh_token_value,
            token_type,
            expires_in,
          } as any,
        }
      }
      
      throw new Error('Registration failed')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }
  
  const logout = async (): Promise<void> => {
    isLoading.value = true
    error.value = null
    
    try {
      // Use backend API for logout
      await apiClient.post('/auth/logout')
      
      clearAuthState()
    } catch (err) {
      console.error('Logout error:', err)
      error.value = err instanceof Error ? err.message : 'Logout failed'
      // Clear state even if logout fails
      clearAuthState()
    } finally {
      isLoading.value = false
    }
  }
  
  const forgotPassword = async (email: string): Promise<{ success: boolean; error?: string }> => {
    isLoading.value = true
    error.value = null
    
    try {
      const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })
      
      if (authError) {
        throw authError
      }
      
      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password reset failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }
  
  const resetPassword = async (
    accessToken: string, 
    refreshToken: string,
    newPassword: string
  ): Promise<{ success: boolean; error?: string }> => {
    isLoading.value = true
    error.value = null
    
    try {
      // Set the session first
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      })
      
      if (sessionError) {
        throw sessionError
      }
      
      // Update the password
      const { error: authError } = await supabase.auth.updateUser({
        password: newPassword,
      })
      
      if (authError) {
        throw authError
      }
      
      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password update failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }

  const loginWithProvider = async (provider: 'google' | 'github'): Promise<{ success: boolean; error?: string }> => {
    isLoading.value = true
    error.value = null
    
    try {
      const { error: authError } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      })
      
      if (authError) {
        throw authError
      }
      
      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : `${provider} login failed`
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }

  const updatePassword = async (currentPassword: string, newPassword: string): Promise<{ success: boolean; error?: string }> => {
    if (!user.value) {
      return { success: false, error: 'User not authenticated' }
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      // First verify current password by attempting to sign in
      const { error: verifyError } = await supabase.auth.signInWithPassword({
        email: user.value.email!,
        password: currentPassword,
      })
      
      if (verifyError) {
        throw new Error('Current password is incorrect')
      }
      
      // Update password
      const { error: updateError } = await supabase.auth.updateUser({
        password: newPassword,
      })
      
      if (updateError) {
        throw updateError
      }
      
      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password update failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }

  const updateUser = (userData: any) => {
    if (user.value) {
      user.value = { ...user.value, ...userData }
    }
    if (profile.value) {
      profile.value = { ...profile.value, ...userData }
    }
  }

  const deleteAccount = async (): Promise<{ success: boolean; error?: string }> => {
    if (!user.value) {
      return { success: false, error: 'User not authenticated' }
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      // Call backend to delete user data
      await apiClient.delete('/users/account')
      
      // Sign out from Supabase
      const { error: signOutError } = await supabase.auth.signOut()
      
      if (signOutError) {
        throw signOutError
      }
      
      clearAuthState()
      
      return { success: true }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Account deletion failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }
  
  const updateProfile = async (updates: Partial<UserProfile>): Promise<{ success: boolean; error?: string }> => {
    if (!user.value) {
      return { success: false, error: 'User not authenticated' }
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      const response = await apiClient.put('/users/profile', updates)
      
      if (response.data) {
        profile.value = { ...profile.value, ...response.data }
        return { success: true }
      }
      
      throw new Error('Profile update failed')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Profile update failed'
      error.value = errorMessage
      
      return {
        success: false,
        error: errorMessage,
      }
    } finally {
      isLoading.value = false
    }
  }
  
  const fetchUserProfile = async (): Promise<void> => {
    if (!user.value) return
    
    try {
      const response = await apiClient.get('/users/me/profile')
      
      if (response.data) {
        profile.value = response.data
      }
    } catch (err) {
      console.error('Failed to fetch user profile:', err)
    }
  }
  
  const createUserProfile = async (profileData: UserProfile): Promise<void> => {
    try {
      const response = await apiClient.post('/users/me', profileData)
      
      if (response.data) {
        profile.value = response.data
      }
    } catch (err) {
      console.error('Failed to create user profile:', err)
    }
  }
  
  const refreshAccessToken = async (): Promise<boolean> => {
    try {
      if (!refreshToken.value) {
        return false
      }
      
      const response = await apiClient.post('/auth/refresh', {
        refresh_token: refreshToken.value,
      })
      
      if (response.data) {
        const { access_token, refresh_token: new_refresh_token } = response.data
        accessToken.value = access_token
        refreshToken.value = new_refresh_token
        return true
      }
      
      return false
    } catch (err) {
      console.error('Token refresh failed:', err)
      return false
    }
  }
  
  const clearAuthState = (): void => {
    user.value = null
    profile.value = null
    accessToken.value = null
    refreshToken.value = null
    error.value = null
  }
  
  const clearError = (): void => {
    error.value = null
  }
  
  // Auth state change callback - no longer using Supabase auth
  const onAuthStateChange = (callback: (user: User | null) => void) => {
    // Return a no-op unsubscribe function
    return { data: { subscription: { unsubscribe: () => {} } } }
  }
  
  return {
    // State
    user: readonly(user),
    profile: readonly(profile),
    isInitialized: readonly(isInitialized),
    isLoading: readonly(isLoading),
    error: readonly(error),
    accessToken: readonly(accessToken),
    refreshToken: readonly(refreshToken),
    
    // Getters
    isAuthenticated,
    userEmail,
    userName,
    userAvatar,
    subscriptionTier,
    hasActiveSubscription,
    
    // Actions
    initializeAuth,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    loginWithProvider,
    updatePassword,
    updateUser,
    deleteAccount,
    updateProfile,
    fetchUserProfile,
    refreshAccessToken,
    clearAuthState,
    clearError,
    onAuthStateChange,
  }
}, {
  persist: {
    storage: localStorage,
    paths: ['user', 'profile', 'accessToken', 'refreshToken'],
  },
})