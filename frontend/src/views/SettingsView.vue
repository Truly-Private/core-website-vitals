<template>
  <div class="settings-view">
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Settings</h1>
        <p class="mt-2 text-gray-600">Manage your account settings and preferences</p>
      </div>

      <!-- Settings Tabs -->
      <div class="border-b border-gray-200 mb-8">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="space-y-6">
        <!-- Profile Settings -->
        <div v-if="activeTab === 'profile'" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Profile Information</h2>
          <form @submit.prevent="updateProfile" class="space-y-4">
            <div>
              <label for="fullName" class="block text-sm font-medium text-gray-700">Full Name</label>
              <input
                id="fullName"
                v-model="profileForm.fullName"
                type="text"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
              <input
                id="email"
                v-model="profileForm.email"
                type="email"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div class="flex justify-end">
              <button
                type="submit"
                :disabled="isLoading"
                class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {{ isLoading ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Notification Settings -->
        <div v-if="activeTab === 'notifications'" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h2>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700">Email Notifications</label>
                <p class="text-sm text-gray-500">Receive notifications via email</p>
              </div>
              <input
                v-model="notificationForm.emailNotifications"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700">Analysis Complete</label>
                <p class="text-sm text-gray-500">Notify when analysis is complete</p>
              </div>
              <input
                v-model="notificationForm.analysisComplete"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
            <div class="flex items-center justify-between">
              <div>
                <label class="text-sm font-medium text-gray-700">Weekly Reports</label>
                <p class="text-sm text-gray-500">Receive weekly analysis summaries</p>
              </div>
              <input
                v-model="notificationForm.weeklyReports"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
            <div class="flex justify-end">
              <button
                @click="updateNotifications"
                :disabled="isLoading"
                class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {{ isLoading ? 'Saving...' : 'Save Preferences' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Analysis Settings -->
        <div v-if="activeTab === 'analysis'" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Analysis Preferences</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Default Analysis Type</label>
              <select
                v-model="analysisForm.defaultType"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="full_seo">Full SEO Analysis</option>
                <option value="technical_seo">Technical SEO</option>
                <option value="content_analysis">Content Analysis</option>
                <option value="performance_audit">Performance Audit</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Max Concurrent Analyses</label>
              <input
                v-model.number="analysisForm.maxConcurrent"
                type="number"
                min="1"
                max="10"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div class="flex items-center">
              <input
                v-model="analysisForm.autoRetry"
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label class="ml-2 text-sm text-gray-700">Auto-retry failed analyses</label>
            </div>
            <div class="flex justify-end">
              <button
                @click="updateAnalysisSettings"
                :disabled="isLoading"
                class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {{ isLoading ? 'Saving...' : 'Save Settings' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Security Settings -->
        <div v-if="activeTab === 'security'" class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">Security Settings</h2>
          <div class="space-y-6">
            <!-- Change Password -->
            <div>
              <h3 class="text-md font-medium text-gray-800 mb-3">Change Password</h3>
              <form @submit.prevent="changePassword" class="space-y-4">
                <div>
                  <label for="currentPassword" class="block text-sm font-medium text-gray-700">Current Password</label>
                  <input
                    id="currentPassword"
                    v-model="passwordForm.currentPassword"
                    type="password"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label for="newPassword" class="block text-sm font-medium text-gray-700">New Password</label>
                  <input
                    id="newPassword"
                    v-model="passwordForm.newPassword"
                    type="password"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirm New Password</label>
                  <input
                    id="confirmPassword"
                    v-model="passwordForm.confirmPassword"
                    type="password"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    required
                  />
                </div>
                <div class="flex justify-end">
                  <button
                    type="submit"
                    :disabled="isLoading"
                    class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {{ isLoading ? 'Changing...' : 'Change Password' }}
                  </button>
                </div>
              </form>
            </div>

            <!-- Danger Zone -->
            <div class="border-t pt-6">
              <h3 class="text-md font-medium text-red-600 mb-3">Danger Zone</h3>
              <div class="bg-red-50 border border-red-200 rounded-md p-4">
                <p class="text-sm text-red-700 mb-3">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
                <button
                  @click="showDeleteConfirmation = true"
                  class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
                >
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteConfirmation" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div class="mt-3 text-center">
          <h3 class="text-lg font-medium text-gray-900">Delete Account</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">
              Are you sure you want to delete your account? This action cannot be undone.
            </p>
          </div>
          <div class="flex justify-center space-x-3 mt-4">
            <button
              @click="showDeleteConfirmation = false"
              class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
            <button
              @click="deleteAccount"
              class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const isLoading = ref(false)
const showDeleteConfirmation = ref(false)
const activeTab = ref('profile')

const tabs = [
  { id: 'profile', label: 'Profile' },
  { id: 'notifications', label: 'Notifications' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'security', label: 'Security' }
]

const profileForm = reactive({
  fullName: '',
  email: ''
})

const notificationForm = reactive({
  emailNotifications: true,
  analysisComplete: true,
  weeklyReports: false
})

const analysisForm = reactive({
  defaultType: 'full_seo',
  maxConcurrent: 5,
  autoRetry: true
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

onMounted(() => {
  // Initialize form data with current user data
  if (authStore.profile) {
    profileForm.fullName = authStore.profile.full_name || ''
    profileForm.email = authStore.userEmail
  }
})

const updateProfile = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    const result = await authStore.updateProfile({
      full_name: profileForm.fullName,
      email: profileForm.email
    })
    
    if (result.success) {
      alert('Profile updated successfully!')
    } else {
      alert('Failed to update profile: ' + result.error)
    }
  } catch (error) {
    console.error('Profile update error:', error)
    alert('Failed to update profile')
  } finally {
    isLoading.value = false
  }
}

const updateNotifications = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    // This would call an API to update notification preferences
    // For now, just simulate the update
    await new Promise(resolve => setTimeout(resolve, 1000))
    alert('Notification preferences updated!')
  } catch (error) {
    console.error('Notification update error:', error)
    alert('Failed to update notification preferences')
  } finally {
    isLoading.value = false
  }
}

const updateAnalysisSettings = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    // This would call an API to update analysis settings
    // For now, just simulate the update
    await new Promise(resolve => setTimeout(resolve, 1000))
    alert('Analysis settings updated!')
  } catch (error) {
    console.error('Analysis settings update error:', error)
    alert('Failed to update analysis settings')
  } finally {
    isLoading.value = false
  }
}

const changePassword = async () => {
  if (isLoading.value) return
  
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    alert('New passwords do not match')
    return
  }
  
  isLoading.value = true
  try {
    const result = await authStore.updatePassword(
      passwordForm.currentPassword,
      passwordForm.newPassword
    )
    
    if (result.success) {
      alert('Password changed successfully!')
      // Clear form
      passwordForm.currentPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
    } else {
      alert('Failed to change password: ' + result.error)
    }
  } catch (error) {
    console.error('Password change error:', error)
    alert('Failed to change password')
  } finally {
    isLoading.value = false
  }
}

const deleteAccount = async () => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    const result = await authStore.deleteAccount()
    
    if (result.success) {
      alert('Account deleted successfully')
      router.push('/')
    } else {
      alert('Failed to delete account: ' + result.error)
    }
  } catch (error) {
    console.error('Account deletion error:', error)
    alert('Failed to delete account')
  } finally {
    isLoading.value = false
    showDeleteConfirmation.value = false
  }
}
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background-color: #f9fafb;
}
</style>