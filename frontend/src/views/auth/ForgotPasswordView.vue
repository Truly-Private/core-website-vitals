<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isLoading = ref(false)
const emailSent = ref(false)

const form = reactive({
  email: ''
})

const errors = reactive({
  email: '',
  general: ''
})

onMounted(() => {
  // Redirect to dashboard if already authenticated
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  }
})

const validateForm = () => {
  errors.email = ''
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
  
  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isLoading.value = true
  
  try {
    await authStore.forgotPassword(form.email)
    emailSent.value = true
    uiStore.showNotification('Password reset email sent successfully!', 'success')
  } catch (error: any) {
    console.error('Forgot password error:', error)
    
    // Handle specific error messages
    if (error.message?.includes('User not found')) {
      errors.general = 'No account found with this email address'
    } else if (error.message?.includes('Rate limit exceeded')) {
      errors.general = 'Too many requests. Please try again later.'
    } else {
      errors.general = 'An error occurred. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

const handleResend = () => {
  emailSent.value = false
  handleSubmit()
}

const goBack = () => {
  router.push({ name: 'login' })
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
          {{ $t('auth.forgot_password.title') }}
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          {{ $t('auth.forgot_password.subtitle') }}
        </p>
      </div>

      <!-- Email Sent Success State -->
      <div v-if="emailSent" class="text-center">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
          <i class="lucide-check w-6 h-6 text-green-600"></i>
        </div>
        
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          Check your email
        </h3>
        
        <p class="text-sm text-gray-600 mb-6">
          We've sent a password reset link to <strong>{{ form.email }}</strong>
        </p>
        
        <div class="space-y-4">
          <button
            @click="handleResend"
            :disabled="isLoading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-primary-600 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <span v-if="isLoading" class="mr-2">
              <i class="lucide-loader-2 w-4 h-4 animate-spin"></i>
            </span>
            {{ isLoading ? $t('common.loading') : 'Resend email' }}
          </button>
          
          <button
            @click="goBack"
            class="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <i class="lucide-arrow-left w-4 h-4 mr-2"></i>
            {{ $t('auth.forgot_password.back_to_login') }}
          </button>
        </div>
      </div>

      <!-- Email Input Form -->
      <form v-else class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">
            {{ $t('auth.forgot_password.email') }}
          </label>
          <input
            id="email"
            v-model="form.email"
            name="email"
            type="email"
            autocomplete="email"
            required
            class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            :class="{ 'border-red-300': errors.email }"
            :placeholder="$t('auth.forgot_password.email')"
          />
          <div v-if="errors.email" class="mt-1 text-sm text-red-600">
            {{ errors.email }}
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
            {{ isLoading ? $t('common.loading') : $t('auth.forgot_password.send_reset') }}
          </button>
        </div>

        <div class="text-center">
          <button
            type="button"
            @click="goBack"
            class="font-medium text-primary-600 hover:text-primary-500"
          >
            <i class="lucide-arrow-left w-4 h-4 mr-1 inline"></i>
            {{ $t('auth.forgot_password.back_to_login') }}
          </button>
        </div>
      </form>

      <!-- Help Text -->
      <div class="text-center">
        <div class="text-sm text-gray-500">
          <p class="mb-2">
            Can't find the email? Check your spam folder or contact support.
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

/* Success state animation */
.bg-green-100 {
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
</style>