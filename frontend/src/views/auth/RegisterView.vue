<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import PublicHeader from '@/components/layout/PublicHeader.vue'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isLoading = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const acceptTerms = ref(false)

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  terms: '',
  general: ''
})

onMounted(() => {
  // Redirect to dashboard if already authenticated
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  }
})

const validateForm = () => {
  // Reset errors
  Object.keys(errors).forEach(key => {
    errors[key as keyof typeof errors] = ''
  })
  
  let isValid = true
  
  // Full name validation
  if (!form.fullName.trim()) {
    errors.fullName = 'Full name is required'
    isValid = false
  } else if (form.fullName.trim().length < 2) {
    errors.fullName = 'Full name must be at least 2 characters'
    isValid = false
  }
  
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
  
  // Terms acceptance validation
  if (!acceptTerms.value) {
    errors.terms = 'You must accept the terms and privacy policy'
    isValid = false
  }
  
  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isLoading.value = true
  
  try {
    const response = await authStore.register({
      email: form.email,
      password: form.password,
      fullName: form.fullName,
      acceptTerms: acceptTerms.value
    })
    
    if (response.success) {
      // Redirect to login with success message
      router.push({ 
        name: 'login', 
        query: { message: 'registration_success' } 
      })
      
      uiStore.showNotification('Registration successful! Please check your email to verify your account.', 'success')
    } else {
      // Handle specific error messages
      const errorMessage = response.error || 'Registration failed'
      
      if (errorMessage.includes('User already registered')) {
        errors.general = 'An account with this email already exists'
      } else if (errorMessage.includes('Password should be at least 6 characters')) {
        errors.password = 'Password must be at least 6 characters'
      } else if (errorMessage.includes('Signup requires a valid password')) {
        errors.password = 'Please provide a valid password'
      } else if (errorMessage.includes('Invalid email')) {
        errors.email = 'Please enter a valid email address'
      } else {
        errors.general = errorMessage
      }
    }
  } catch (error: any) {
    console.error('Registration error:', error)
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
</script>

<template>
  <div class="auth-page">
    <PublicHeader />
    <div class="auth-container">
      <div class="auth-card">
      <div>
        <div class="flex justify-center">
          <h1 class="text-3xl font-bold text-primary-600">
            Core Website Vitals
          </h1>
        </div>
        <h2 class="auth-title">
          {{ $t('auth.register.title') }}
        </h2>
        <p class="auth-subtitle">
          {{ $t('auth.register.subtitle') }}
        </p>
      </div>

      <form class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <!-- Full Name -->
          <div>
            <label for="fullName" class="form-label">
              {{ $t('auth.register.full_name') }}
            </label>
            <input
              id="fullName"
              v-model="form.fullName"
              name="fullName"
              type="text"
              autocomplete="name"
              required
              class="form-input"
              :class="{ 'border-red-300': errors.fullName }"
              :placeholder="$t('auth.register.full_name')"
            />
            <div v-if="errors.fullName" class="mt-1 text-sm text-red-600">
              {{ errors.fullName }}
            </div>
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="form-label">
              {{ $t('auth.register.email') }}
            </label>
            <input
              id="email"
              v-model="form.email"
              name="email"
              type="email"
              autocomplete="email"
              required
              class="form-input"
              :class="{ 'border-red-300': errors.email }"
              :placeholder="$t('auth.register.email')"
            />
            <div v-if="errors.email" class="mt-1 text-sm text-red-600">
              {{ errors.email }}
            </div>
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="form-label">
              {{ $t('auth.register.password') }}
            </label>
            <div class="relative">
              <input
                id="password"
                v-model="form.password"
                name="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                class="form-input pr-10"
                :class="{ 'border-red-300': errors.password }"
                :placeholder="$t('auth.register.password')"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="togglePasswordVisibility('password')"
              >
                <i 
                  :class="showPassword ? 'lucide-eye-off' : 'lucide-eye'"
                  class="w-5 h-5 icon-secondary"
                ></i>
              </button>
            </div>
            
            <!-- Password Strength Indicator -->
            <div v-if="form.password" class="mt-2">
              <div class="flex items-center space-x-2">
                <div class="flex-1 strength-track rounded-full h-2">
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
                <span class="text-xs strength-text">{{ passwordStrength.text }}</span>
              </div>
            </div>
            
            <div v-if="errors.password" class="mt-1 text-sm text-red-600">
              {{ errors.password }}
            </div>
          </div>

          <!-- Confirm Password -->
          <div>
            <label for="confirmPassword" class="form-label">
              {{ $t('auth.register.confirm_password') }}
            </label>
            <div class="relative">
              <input
                id="confirmPassword"
                v-model="form.confirmPassword"
                name="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                class="form-input pr-10"
                :class="{ 'border-red-300': errors.confirmPassword }"
                :placeholder="$t('auth.register.confirm_password')"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 pr-3 flex items-center"
                @click="togglePasswordVisibility('confirmPassword')"
              >
                <i 
                  :class="showConfirmPassword ? 'lucide-eye-off' : 'lucide-eye'"
                  class="w-5 h-5 icon-secondary"
                ></i>
              </button>
            </div>
            <div v-if="errors.confirmPassword" class="mt-1 text-sm text-red-600">
              {{ errors.confirmPassword }}
            </div>
          </div>

          <!-- Terms and Privacy -->
          <div>
            <div class="flex items-center">
              <input
                id="terms"
                v-model="acceptTerms"
                name="terms"
                type="checkbox"
                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                :class="{ 'border-red-300': errors.terms }"
              />
              <label for="terms" class="ml-2 block text-sm form-text">
                I accept the
                <a href="#" class="text-primary-600 hover:text-primary-500">Terms of Service</a>
                and
                <a href="#" class="text-primary-600 hover:text-primary-500">Privacy Policy</a>
              </label>
            </div>
            <div v-if="errors.terms" class="mt-1 text-sm text-red-600">
              {{ errors.terms }}
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
            {{ isLoading ? $t('common.loading') : $t('auth.register.create_account') }}
          </button>
        </div>

        <div class="mt-6">
          <div class="relative">
            <div class="absolute inset-0 flex items-center">
              <div class="w-full border-t divider-line" />
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 divider-text">{{ $t('auth.login.or') }}</span>
            </div>
          </div>

          <div class="mt-6 grid grid-cols-2 gap-3">
            <button
              type="button"
              @click="handleSocialLogin('google')"
              class="social-button"
            >
              <i class="lucide-mail w-5 h-5 text-red-500"></i>
              <span class="ml-2">Google</span>
            </button>

            <button
              type="button"
              @click="handleSocialLogin('github')"
              class="social-button"
            >
              <i class="lucide-github w-5 h-5 text-gray-900"></i>
              <span class="ml-2">GitHub</span>
            </button>
          </div>
        </div>

        <div class="text-center">
          <p class="text-sm form-text">
            {{ $t('auth.register.already_have_account') }}
            <router-link
              :to="{ name: 'login' }"
              class="font-medium text-primary-600 hover:text-primary-500"
            >
              {{ $t('auth.register.sign_in') }}
            </router-link>
          </p>
        </div>
      </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Auth page layout */
.auth-page {
  min-height: 100vh;
  background-color: var(--color-background);
}

.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px);
  padding: 3rem 1rem;
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

.auth-title {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 1.875rem;
  font-weight: 800;
  color: var(--color-text-primary);
}

.auth-subtitle {
  margin-top: 0.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* Form styles */
.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.form-input {
  margin-top: 0.25rem;
  appearance: none;
  position: relative;
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  transition: all var(--transition-fast);
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
}

.form-input.border-red-300 {
  border-color: rgb(252 165 165);
}

/* Icons */
.icon-secondary {
  color: var(--color-text-tertiary);
}

/* Password strength */
.strength-track {
  background-color: var(--color-surface-variant);
}

.strength-text {
  color: var(--color-text-secondary);
}

/* Terms checkbox */
.form-text {
  color: var(--color-text-primary);
}

/* Divider */
.divider-line {
  border-color: var(--color-border);
}

.divider-text {
  padding: 0 0.5rem;
  background-color: var(--color-surface);
  color: var(--color-text-tertiary);
}

/* Social buttons */
.social-button {
  width: 100%;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  background-color: var(--color-surface);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.social-button:hover {
  background-color: var(--color-surface-variant);
  border-color: var(--color-primary);
}

/* Primary button */
.btn-primary {
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* Password strength indicator transitions */
.transition-all {
  transition: all 0.3s ease-in-out;
}

/* Error text */
.text-red-600 {
  color: rgb(220 38 38);
}
</style>