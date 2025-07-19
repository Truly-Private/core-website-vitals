<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import PublicHeader from '@/components/layout/PublicHeader.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isLoading = ref(false)
const showPassword = ref(false)
const rememberMe = ref(false)

const form = reactive({
  email: '',
  password: ''
})

const errors = reactive({
  email: '',
  password: '',
  general: ''
})

onMounted(() => {
  // Redirect to dashboard if already authenticated
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  }
  
  // Check for success message from registration
  if (route.query.message === 'registration_success') {
    uiStore.showNotification('Please check your email to verify your account', 'success')
  }
})

const validateForm = () => {
  // Reset errors
  errors.email = ''
  errors.password = ''
  errors.general = ''
  
  let isValid = true
  
  // Email validation
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Please enter a valid email address'
    isValid = false
  }
  
  // Password validation
  if (!form.password) {
    errors.password = 'Password is required'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = 'Password must be at least 6 characters'
    isValid = false
  }
  
  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isLoading.value = true
  
  try {
    const response = await authStore.login({
      email: form.email,
      password: form.password
    })
    
    if (response.success) {
      // Redirect to intended page or dashboard
      const redirectTo = route.query.redirect as string || 'dashboard'
      router.push({ name: redirectTo })
      
      uiStore.showNotification('Welcome back!', 'success')
    } else {
      // Handle specific error messages
      const errorMessage = response.error || 'An error occurred during login'
      
      if (errorMessage.includes('Invalid login credentials')) {
        errors.general = 'Invalid email or password'
      } else if (errorMessage.includes('Email not confirmed')) {
        errors.general = 'Please verify your email address before logging in'
      } else if (errorMessage.includes('Too many requests')) {
        errors.general = 'Too many login attempts. Please try again later'
      } else {
        errors.general = errorMessage
      }
    }
  } catch (error: any) {
    console.error('Login error:', error)
    errors.general = 'An unexpected error occurred. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const handleSocialLogin = async (provider: 'google' | 'github') => {
  try {
    await authStore.loginWithProvider(provider)
  } catch (error) {
    console.error(`${provider} login error:`, error)
    uiStore.showNotification(`Failed to login with ${provider}`, 'error')
  }
}

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}
</script>

<template>
  <div class="auth-page">
    <PublicHeader />
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h2 class="auth-title">
            {{ $t('auth.login.title') }}
          </h2>
          <p class="auth-subtitle">
            {{ $t('auth.login.subtitle') }}
          </p>
        </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="rounded-md shadow-sm -space-y-px">
          <div>
            <label for="email" class="sr-only">{{ $t('auth.login.email') }}</label>
            <input
              id="email"
              v-model="form.email"
              name="email"
              type="email"
              autocomplete="email"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              :class="{ 'border-red-300': errors.email }"
              :placeholder="$t('auth.login.email')"
            />
            <div v-if="errors.email" class="mt-1 text-sm text-red-600">
              {{ errors.email }}
            </div>
          </div>
          
          <div class="relative">
            <label for="password" class="sr-only">{{ $t('auth.login.password') }}</label>
            <input
              id="password"
              v-model="form.password"
              name="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
              class="appearance-none rounded-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
              :class="{ 'border-red-300': errors.password }"
              :placeholder="$t('auth.login.password')"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 pr-3 flex items-center"
              @click="togglePasswordVisibility"
            >
              <i 
                :class="showPassword ? 'lucide-eye-off' : 'lucide-eye'"
                class="w-5 h-5 text-gray-400"
              ></i>
            </button>
            <div v-if="errors.password" class="mt-1 text-sm text-red-600">
              {{ errors.password }}
            </div>
          </div>
        </div>

        <div v-if="errors.general" class="text-sm text-red-600 text-center">
          {{ errors.general }}
        </div>

        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              v-model="rememberMe"
              name="remember-me"
              type="checkbox"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label for="remember-me" class="ml-2 block text-sm text-gray-900">
              {{ $t('auth.login.remember_me') }}
            </label>
          </div>

          <div class="text-sm">
            <router-link
              :to="{ name: 'forgot-password' }"
              class="font-medium text-primary-600 hover:text-primary-500"
            >
              {{ $t('auth.login.forgot_password') }}
            </router-link>
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading" class="absolute left-0 inset-y-0 flex items-center pl-3">
              <i class="lucide-loader-2 w-5 h-5 animate-spin"></i>
            </span>
            {{ isLoading ? $t('common.loading') : $t('auth.login.sign_in') }}
          </button>
        </div>

        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t border-gray-300" />
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-gray-50 text-gray-500">{{ $t('auth.login.or') }}</span>
            </div>
          </div>

          <div class="mt-6 grid grid-cols-2 gap-3">
            <button
              type="button"
              @click="handleSocialLogin('google')"
              class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
            >
              <i class="lucide-mail w-5 h-5 text-red-500"></i>
              <span class="ml-2">{{ $t('auth.login.google') }}</span>
            </button>

            <button
              type="button"
              @click="handleSocialLogin('github')"
              class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
            >
              <i class="lucide-github w-5 h-5 text-gray-900"></i>
              <span class="ml-2">{{ $t('auth.login.github') }}</span>
            </button>
          </div>
        </div>

        <div class="text-center">
          <p class="text-sm text-gray-600">
            {{ $t('auth.login.no_account') }}
            <router-link
              :to="{ name: 'register' }"
              class="font-medium text-primary-600 hover:text-primary-500"
            >
              {{ $t('auth.login.sign_up') }}
            </router-link>
          </p>
        </div>
      </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  background-color: var(--color-background);
}

.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: var(--spacing-2xl) var(--spacing-lg);
}

.auth-card {
  width: 100%;
  max-width: 448px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--spacing-2xl);
  box-shadow: var(--shadow-lg);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.auth-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-sm) 0;
}

.auth-subtitle {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Form styles with theme support */
.form-input {
  background-color: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.form-input:focus {
  border-color: var(--color-primary);
  background-color: var(--color-surface);
}

/* Custom loading animation */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Focus states */
input:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Transition effects */
button, input {
  transition: all 0.2s ease-in-out;
}
</style>