<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

const activeTab = ref('profile')
const isLoading = ref(false)
const isUpdatingPassword = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const profileForm = reactive({
  fullName: '',
  email: '',
  timezone: '',
  language: 'en',
  avatar: null as File | null
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileErrors = reactive({
  fullName: '',
  email: '',
  general: ''
})

const passwordErrors = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  general: ''
})

const tabs = [
  { id: 'profile', name: 'Profile', icon: 'user' },
  { id: 'security', name: 'Security', icon: 'shield' },
  { id: 'preferences', name: 'Preferences', icon: 'settings' },
  { id: 'subscription', name: 'Subscription', icon: 'credit-card' }
]

const timezones = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' }
]

const languages = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' }
]

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  loadUserProfile()
})

const loadUserProfile = () => {
  if (authStore.user) {
    profileForm.fullName = authStore.user.user_metadata?.full_name || ''
    profileForm.email = authStore.user.email || ''
    profileForm.timezone = authStore.user.user_metadata?.timezone || 'UTC'
    profileForm.language = authStore.user.user_metadata?.language || 'en'
  }
}

const validateProfileForm = () => {
  // Reset errors
  Object.keys(profileErrors).forEach(key => {
    profileErrors[key as keyof typeof profileErrors] = ''
  })
  
  let isValid = true
  
  // Full name validation
  if (!profileForm.fullName.trim()) {
    profileErrors.fullName = 'Full name is required'
    isValid = false
  } else if (profileForm.fullName.trim().length < 2) {
    profileErrors.fullName = 'Full name must be at least 2 characters'
    isValid = false
  }
  
  // Email validation
  if (!profileForm.email.trim()) {
    profileErrors.email = 'Email is required'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.email)) {
    profileErrors.email = 'Please enter a valid email address'
    isValid = false
  }
  
  return isValid
}

const validatePasswordForm = () => {
  // Reset errors
  Object.keys(passwordErrors).forEach(key => {
    passwordErrors[key as keyof typeof passwordErrors] = ''
  })
  
  let isValid = true
  
  // Current password validation
  if (!passwordForm.currentPassword) {
    passwordErrors.currentPassword = 'Current password is required'
    isValid = false
  }
  
  // New password validation
  if (!passwordForm.newPassword) {
    passwordErrors.newPassword = 'New password is required'
    isValid = false
  } else if (passwordForm.newPassword.length < 8) {
    passwordErrors.newPassword = 'Password must be at least 8 characters'
    isValid = false
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(passwordForm.newPassword)) {
    passwordErrors.newPassword = 'Password must contain at least one lowercase letter, one uppercase letter, and one number'
    isValid = false
  }
  
  // Confirm password validation
  if (!passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = 'Please confirm your new password'
    isValid = false
  } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordErrors.confirmPassword = 'Passwords do not match'
    isValid = false
  }
  
  return isValid
}

const handleProfileSubmit = async () => {
  if (!validateProfileForm()) return
  
  isLoading.value = true
  
  try {
    await authStore.updateProfile({
      full_name: profileForm.fullName,
      email: profileForm.email,
      timezone: profileForm.timezone,
      language: profileForm.language
    })
    
    uiStore.showNotification('Profile updated successfully!', 'success')
  } catch (error: any) {
    console.error('Profile update error:', error)
    
    if (error.message?.includes('Email already exists')) {
      profileErrors.email = 'This email is already in use'
    } else {
      profileErrors.general = 'An error occurred while updating your profile. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

const handlePasswordSubmit = async () => {
  if (!validatePasswordForm()) return
  
  isUpdatingPassword.value = true
  
  try {
    await authStore.updatePassword(passwordForm.currentPassword, passwordForm.newPassword)
    
    // Clear form
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    
    uiStore.showNotification('Password updated successfully!', 'success')
  } catch (error: any) {
    console.error('Password update error:', error)
    
    if (error.message?.includes('Invalid password')) {
      passwordErrors.currentPassword = 'Current password is incorrect'
    } else {
      passwordErrors.general = 'An error occurred while updating your password. Please try again.'
    }
  } finally {
    isUpdatingPassword.value = false
  }
}

const handleAvatarUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      uiStore.showNotification('Please select an image file', 'error')
      return
    }
    
    // Validate file size (5MB limit)
    if (file.size > 5 * 1024 * 1024) {
      uiStore.showNotification('Image must be less than 5MB', 'error')
      return
    }
    
    profileForm.avatar = file
    uiStore.showNotification('Avatar will be updated when you save your profile', 'info')
  }
}

const togglePasswordVisibility = (field: 'current' | 'new' | 'confirm') => {
  switch (field) {
    case 'current':
      showCurrentPassword.value = !showCurrentPassword.value
      break
    case 'new':
      showNewPassword.value = !showNewPassword.value
      break
    case 'confirm':
      showConfirmPassword.value = !showConfirmPassword.value
      break
  }
}

const goToBilling = () => {
  router.push({ name: 'billing' })
}

const deleteAccount = async () => {
  const confirmed = await uiStore.showConfirmDialog(
    'Delete Account',
    'Are you sure you want to delete your account? This action cannot be undone.',
    'Delete',
    'danger'
  )
  
  if (confirmed) {
    try {
      await authStore.deleteAccount()
      uiStore.showNotification('Account deleted successfully', 'success')
      router.push({ name: 'home' })
    } catch (error) {
      console.error('Delete account error:', error)
      uiStore.showNotification('Failed to delete account', 'error')
    }
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">
              {{ $t('profile.title') }}
            </h1>
          </div>
          
          <div class="flex items-center space-x-4">
            <router-link
              :to="{ name: 'dashboard' }"
              class="btn btn-outline"
            >
              <i class="lucide-arrow-left w-4 h-4 mr-2"></i>
              Back to Dashboard
            </router-link>
          </div>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="lg:grid lg:grid-cols-12 lg:gap-8">
        <!-- Sidebar -->
        <div class="lg:col-span-3">
          <nav class="space-y-1" aria-label="Sidebar">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                activeTab === tab.id
                  ? 'bg-primary-50 border-primary-500 text-primary-700'
                  : 'border-transparent text-gray-900 hover:bg-gray-50 hover:text-gray-900',
                'group border-l-4 px-3 py-2 flex items-center text-sm font-medium w-full'
              ]"
            >
              <i :class="`lucide-${tab.icon} w-5 h-5 mr-3`"></i>
              {{ tab.name }}
            </button>
          </nav>
        </div>

        <!-- Main Content -->
        <div class="mt-8 lg:mt-0 lg:col-span-9">
          <!-- Profile Tab -->
          <div v-if="activeTab === 'profile'" class="space-y-6">
            <div class="bg-white shadow rounded-lg">
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  {{ $t('profile.personal_info') }}
                </h3>
                <p class="mt-1 text-sm text-gray-500">
                  Update your personal information and profile settings.
                </p>
                
                <form @submit.prevent="handleProfileSubmit" class="mt-6 space-y-4">
                  <!-- Avatar Upload -->
                  <div class="flex items-center space-x-6">
                    <div class="flex-shrink-0">
                      <img
                        :src="authStore.user?.user_metadata?.avatar_url || '/avatars/default.svg'"
                        :alt="authStore.user?.user_metadata?.full_name || 'User Avatar'"
                        class="h-16 w-16 rounded-full object-cover"
                      />
                    </div>
                    <div>
                      <label for="avatar" class="block text-sm font-medium text-gray-700">
                        Profile Photo
                      </label>
                      <input
                        id="avatar"
                        type="file"
                        accept="image/*"
                        @change="handleAvatarUpload"
                        class="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                      />
                    </div>
                  </div>

                  <!-- Full Name -->
                  <div>
                    <label for="fullName" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.fields.full_name') }}
                    </label>
                    <input
                      id="fullName"
                      v-model="profileForm.fullName"
                      type="text"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      :class="{ 'border-red-300': profileErrors.fullName }"
                    />
                    <div v-if="profileErrors.fullName" class="mt-1 text-sm text-red-600">
                      {{ profileErrors.fullName }}
                    </div>
                  </div>

                  <!-- Email -->
                  <div>
                    <label for="email" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.fields.email') }}
                    </label>
                    <input
                      id="email"
                      v-model="profileForm.email"
                      type="email"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      :class="{ 'border-red-300': profileErrors.email }"
                    />
                    <div v-if="profileErrors.email" class="mt-1 text-sm text-red-600">
                      {{ profileErrors.email }}
                    </div>
                  </div>

                  <!-- Timezone -->
                  <div>
                    <label for="timezone" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.fields.timezone') }}
                    </label>
                    <select
                      id="timezone"
                      v-model="profileForm.timezone"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option v-for="timezone in timezones" :key="timezone.value" :value="timezone.value">
                        {{ timezone.label }}
                      </option>
                    </select>
                  </div>

                  <!-- Language -->
                  <div>
                    <label for="language" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.fields.language') }}
                    </label>
                    <select
                      id="language"
                      v-model="profileForm.language"
                      class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    >
                      <option v-for="language in languages" :key="language.value" :value="language.value">
                        {{ language.label }}
                      </option>
                    </select>
                  </div>

                  <div v-if="profileErrors.general" class="text-sm text-red-600">
                    {{ profileErrors.general }}
                  </div>

                  <div class="flex justify-end">
                    <button
                      type="submit"
                      :disabled="isLoading"
                      class="btn btn-primary"
                    >
                      <i v-if="isLoading" class="lucide-loader-2 w-4 h-4 mr-2 animate-spin"></i>
                      {{ isLoading ? $t('common.loading') : $t('profile.update_profile') }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>

          <!-- Security Tab -->
          <div v-if="activeTab === 'security'" class="space-y-6">
            <div class="bg-white shadow rounded-lg">
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  {{ $t('profile.change_password') }}
                </h3>
                <p class="mt-1 text-sm text-gray-500">
                  Update your password to keep your account secure.
                </p>
                
                <form @submit.prevent="handlePasswordSubmit" class="mt-6 space-y-4">
                  <!-- Current Password -->
                  <div>
                    <label for="currentPassword" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.current_password') }}
                    </label>
                    <div class="relative">
                      <input
                        id="currentPassword"
                        v-model="passwordForm.currentPassword"
                        :type="showCurrentPassword ? 'text' : 'password'"
                        class="mt-1 block w-full pr-10 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        :class="{ 'border-red-300': passwordErrors.currentPassword }"
                      />
                      <button
                        type="button"
                        class="absolute inset-y-0 right-0 pr-3 flex items-center"
                        @click="togglePasswordVisibility('current')"
                      >
                        <i 
                          :class="showCurrentPassword ? 'lucide-eye-off' : 'lucide-eye'"
                          class="w-5 h-5 text-gray-400"
                        ></i>
                      </button>
                    </div>
                    <div v-if="passwordErrors.currentPassword" class="mt-1 text-sm text-red-600">
                      {{ passwordErrors.currentPassword }}
                    </div>
                  </div>

                  <!-- New Password -->
                  <div>
                    <label for="newPassword" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.new_password') }}
                    </label>
                    <div class="relative">
                      <input
                        id="newPassword"
                        v-model="passwordForm.newPassword"
                        :type="showNewPassword ? 'text' : 'password'"
                        class="mt-1 block w-full pr-10 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        :class="{ 'border-red-300': passwordErrors.newPassword }"
                      />
                      <button
                        type="button"
                        class="absolute inset-y-0 right-0 pr-3 flex items-center"
                        @click="togglePasswordVisibility('new')"
                      >
                        <i 
                          :class="showNewPassword ? 'lucide-eye-off' : 'lucide-eye'"
                          class="w-5 h-5 text-gray-400"
                        ></i>
                      </button>
                    </div>
                    <div v-if="passwordErrors.newPassword" class="mt-1 text-sm text-red-600">
                      {{ passwordErrors.newPassword }}
                    </div>
                  </div>

                  <!-- Confirm Password -->
                  <div>
                    <label for="confirmPassword" class="block text-sm font-medium text-gray-700">
                      {{ $t('profile.confirm_password') }}
                    </label>
                    <div class="relative">
                      <input
                        id="confirmPassword"
                        v-model="passwordForm.confirmPassword"
                        :type="showConfirmPassword ? 'text' : 'password'"
                        class="mt-1 block w-full pr-10 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                        :class="{ 'border-red-300': passwordErrors.confirmPassword }"
                      />
                      <button
                        type="button"
                        class="absolute inset-y-0 right-0 pr-3 flex items-center"
                        @click="togglePasswordVisibility('confirm')"
                      >
                        <i 
                          :class="showConfirmPassword ? 'lucide-eye-off' : 'lucide-eye'"
                          class="w-5 h-5 text-gray-400"
                        ></i>
                      </button>
                    </div>
                    <div v-if="passwordErrors.confirmPassword" class="mt-1 text-sm text-red-600">
                      {{ passwordErrors.confirmPassword }}
                    </div>
                  </div>

                  <div v-if="passwordErrors.general" class="text-sm text-red-600">
                    {{ passwordErrors.general }}
                  </div>

                  <div class="flex justify-end">
                    <button
                      type="submit"
                      :disabled="isUpdatingPassword"
                      class="btn btn-primary"
                    >
                      <i v-if="isUpdatingPassword" class="lucide-loader-2 w-4 h-4 mr-2 animate-spin"></i>
                      {{ isUpdatingPassword ? $t('common.loading') : $t('profile.change_password') }}
                    </button>
                  </div>
                </form>
              </div>
            </div>

            <!-- Danger Zone -->
            <div class="bg-white shadow rounded-lg border border-red-200">
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-red-900">
                  Danger Zone
                </h3>
                <p class="mt-1 text-sm text-red-600">
                  These actions cannot be undone. Please be careful.
                </p>
                
                <div class="mt-6">
                  <button
                    @click="deleteAccount"
                    class="btn btn-danger"
                  >
                    <i class="lucide-trash-2 w-4 h-4 mr-2"></i>
                    Delete Account
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Subscription Tab -->
          <div v-if="activeTab === 'subscription'" class="space-y-6">
            <div class="bg-white shadow rounded-lg">
              <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  {{ $t('profile.subscription') }}
                </h3>
                <p class="mt-1 text-sm text-gray-500">
                  Manage your subscription and billing information.
                </p>
                
                <div class="mt-6">
                  <div class="flex items-center justify-between">
                    <div>
                      <p class="text-sm font-medium text-gray-900">Current Plan</p>
                      <p class="text-sm text-gray-500 capitalize">{{ authStore.subscriptionTier }}</p>
                    </div>
                    <button
                      @click="goToBilling"
                      class="btn btn-primary"
                    >
                      Manage Subscription
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Custom animations */
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
input:focus, select:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Transition effects */
button, input, select {
  transition: all 0.2s ease-in-out;
}

/* File input styling */
input[type="file"]::-webkit-file-upload-button {
  -webkit-appearance: none;
  appearance: none;
}
</style>