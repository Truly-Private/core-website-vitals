<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isLoading = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const resetSuccess = ref(false)
const tokenError = ref(false)

const form = reactive({
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  password: '',
  confirmPassword: '',
  general: ''
})

onMounted(() => {
  // Check if we have the required tokens in the URL
  const accessToken = route.query.access_token as string
  const refreshToken = route.query.refresh_token as string
  
  if (!accessToken || !refreshToken) {
    tokenError.value = true
    return
  }
  
  // Redirect to dashboard if already authenticated
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  }
})

const validateForm = () => {
  errors.password = ''
  errors.confirmPassword = ''
  errors.general = ''
  
  let isValid = true
  
  // Password validation
  if (!form.password) {
    errors.password = 'Password is required'
    isValid = false
  } else if (form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    isValid = false
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(form.password)) {
    errors.password = 'Password must contain at least one lowercase letter, one uppercase letter, and one number'
    isValid = false
  }
  
  // Confirm password validation
  if (!form.confirmPassword) {
    errors.confirmPassword = 'Please confirm your password'
    isValid = false
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
    isValid = false
  }
  
  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isLoading.value = true
  
  try {
    const accessToken = route.query.access_token as string
    const refreshToken = route.query.refresh_token as string
    
    await authStore.resetPassword(accessToken, refreshToken, form.password)
    resetSuccess.value = true
    uiStore.showNotification('Password reset successfully!', 'success')
  } catch (error: any) {
    console.error('Reset password error:', error)
    
    // Handle specific error messages
    if (error.message?.includes('Invalid token') || error.message?.includes('Token expired')) {
      errors.general = 'Reset link is invalid or expired. Please request a new one.'
    } else if (error.message?.includes('Password should be at least 6 characters')) {
      errors.password = 'Password must be at least 6 characters'
    } else {
      errors.general = 'An error occurred while resetting your password. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

const togglePasswordVisibility = (field: 'password' | 'confirmPassword') => {
  if (field === 'password') {
    showPassword.value = !showPassword.value
  } else {
    showConfirmPassword.value = !showConfirmPassword.value
  }
}

const getPasswordStrength = (password: string) => {
  if (!password) return { strength: 0, text: '' }
  
  let strength = 0
  let text = ''
  
  if (password.length >= 8) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/\d/.test(password)) strength++
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++
  
  if (strength < 2) {
    text = 'Weak'
  } else if (strength < 4) {
    text = 'Medium'
  } else {
    text = 'Strong'
  }
  
  return { strength, text }
}

const passwordStrength = computed(() => getPasswordStrength(form.password))

const goToLogin = () => {
  router.push({ name: 'login' })
}

const requestNewReset = () => {
  router.push({ name: 'forgot-password' })
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div>
        <div class="flex justify-center">
          <h1 class="text-3xl font-bold text-primary-600">
            Core Website Vitals
          </h1>
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          {{ $t('auth.reset_password.title') }}
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          {{ $t('auth.reset_password.subtitle') }}
        </p>
      </div>

      <!-- Token Error State -->
      <div v-if="tokenError" class="text-center">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
          <i class="lucide-x w-6 h-6 text-red-600"></i>
        </div>
        
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          Invalid Reset Link
        </h3>
        
        <p class="text-sm text-gray-600 mb-6">
          This password reset link is invalid or has expired. Please request a new one.
        </p>
        
        <div class="space-y-4">
          <button
            @click="requestNewReset"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Request New Reset Link
          </button>
          
          <button
            @click="goToLogin"
            class="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <i class="lucide-arrow-left w-4 h-4 mr-2"></i>
            Back to Login
          </button>
        </div>
      </div>

      <!-- Reset Success State -->
      <div v-else-if="resetSuccess" class="text-center">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
          <i class="lucide-check w-6 h-6 text-green-600"></i>
        </div>
        
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          Password Reset Successful
        </h3>
        
        <p class="text-sm text-gray-600 mb-6">
          Your password has been successfully reset. You can now login with your new password.
        </p>
        
        <button
          @click="goToLogin"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Continue to Login
        </button>
      </div>

      <!-- Password Reset Form -->
      <form v-else class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <!-- New Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              {{ $t('auth.reset_password.password') }}
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                :class="{ 'border-red-300': errors.password }"
                :placeholder="$t('auth.reset_password.password')"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="togglePasswordVisibility('password')"
              >
                <i 
                  :class="showPassword ? 'lucide-eye-off' : 'lucide-eye'"
                  class="w-5 h-5 text-gray-400"
                ></i>
              </button>
            </div>
            
            <!-- Password Strength Indicator -->
            <div v-if="form.password" class="mt-2">
              <div class="flex items-center space-x-2">
                <div class="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    class="h-2 rounded-full transition-all duration-300"
                    :class="{
                      'bg-red-500': passwordStrength.strength <= 2,
                      'bg-yellow-500': passwordStrength.strength === 3,
                      'bg-green-500': passwordStrength.strength >= 4
                    }"
                    :style="{ width: `${(passwordStrength.strength / 5) * 100}%` }"
                  ></div>
                </div>
                <span class="text-xs text-gray-600">{{ passwordStrength.text }}</span>
              </div>
            </div>
            
            <div v-if="errors.password" class="mt-1 text-sm text-red-600">
              {{ errors.password }}
            </div>
          </div>

          <!-- Confirm Password -->
          <div>
            <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
              {{ $t('auth.reset_password.confirm_password') }}
            </label>
            <div class="relative">
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                name="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                class="mt-1 appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                :class="{ 'border-red-300': errors.confirmPassword }"
                :placeholder="$t('auth.reset_password.confirm_password')"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="togglePasswordVisibility('confirmPassword')"
              >
                <i 
                  :class="showConfirmPassword ? 'lucide-eye-off' : 'lucide-eye'"
                  class="w-5 h-5 text-gray-400"
                ></i>
              </button>
            </div>
            <div v-if="errors.confirmPassword" class="mt-1 text-sm text-red-600">
              {{ errors.confirmPassword }}
            </div>
          </div>
        </div>

        <div v-if="errors.general" class="text-sm text-red-600 text-center">
          {{ errors.general }}
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
            {{ isLoading ? $t('common.loading') : $t('auth.reset_password.reset_password') }}
          </button>
        </div>

        <div class="text-center">
          <button
            type="button"
            @click="goToLogin"
            class="font-medium text-primary-600 hover:text-primary-500"
          >
            <i class="lucide-arrow-left w-4 h-4 mr-1 inline"></i>
            Back to Login
          </button>
        </div>
      </form>

      <!-- Help Text -->
      <div class="text-center">
        <div class="text-sm text-gray-500">
          <p class="mb-2">
            Having trouble? Contact our support team.
          </p>
          <a
            href="mailto:support@corewebsitevitals.com"
            class="text-primary-600 hover:text-primary-500"
          >
            support@corewebsitevitals.com
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

/* Success/Error state animations */
.bg-green-100, .bg-red-100 {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* Password strength indicator transitions */
.transition-all {
  transition: all 0.3s ease-in-out;
}
</style>