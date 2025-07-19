<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useToast } from 'vue-toastification'

// Store instances
const authStore = useAuthStore()
const uiStore = useUIStore()
const toast = useToast()
const route = useRoute()
const router = useRouter()

// Initialize app
onMounted(async () => {
  // Initialize auth state
  await authStore.initializeAuth()
  
  // Set up authentication state watcher
  authStore.onAuthStateChange((user) => {
    if (!user && route.meta.requiresAuth) {
      router.push({ name: 'login' })
    }
  })
  
  // Initialize UI theme
  uiStore.initializeTheme()
  
  // Set up app-level event listeners
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  window.addEventListener('beforeunload', handleBeforeUnload)
  
  // Check initial connectivity
  if (!navigator.onLine) {
    handleOffline()
  }
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

// Watch for route changes to handle page title
watch(() => route.meta.title, (newTitle) => {
  if (newTitle) {
    document.title = `${newTitle} - Core Website Vitals`
  } else {
    document.title = 'Core Website Vitals - SEO Analysis Platform'
  }
}, { immediate: true })

// Watch for theme changes
watch(() => uiStore.theme, (newTheme) => {
  if (newTheme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}, { immediate: true })

// Event handlers
const handleOnline = () => {
  uiStore.setOnlineStatus(true)
  toast.success('Connection restored', {
    timeout: 3000,
  })
}

const handleOffline = () => {
  uiStore.setOnlineStatus(false)
  toast.error('No internet connection', {
    timeout: 0, // Don't auto-hide
  })
}

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  // Show confirmation if there are unsaved changes
  if (uiStore.hasUnsavedChanges) {
    event.preventDefault()
    event.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
    return event.returnValue
  }
}

// Error boundary handler
const handleError = (error: Error, errorInfo: any) => {
  console.error('App error boundary caught:', error)
  console.error('Error info:', errorInfo)
  
  // Show user-friendly error message
  toast.error('An unexpected error occurred. Please try again.', {
    timeout: 5000,
  })
  
  // In production, send to error reporting service
  if (import.meta.env.PROD) {
    // Sentry.captureException(error, { extra: errorInfo })
  }
}
</script>

<template>
  <div 
    id="app" 
    :class="[
      'min-h-screen bg-gray-50 transition-colors duration-300',
      {
        'dark:bg-gray-900': uiStore.theme === 'dark'
      }
    ]"
  >
    <!-- Global loading indicator -->
    <div 
      v-if="uiStore.isLoading"
      class="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center space-y-4">
        <div class="spinner spinner-lg text-primary-600"></div>
        <p class="text-sm text-gray-600">{{ uiStore.loadingMessage || 'Loading...' }}</p>
      </div>
    </div>
    
    <!-- Offline indicator -->
    <div 
      v-if="!uiStore.isOnline"
      class="fixed top-0 left-0 right-0 z-40 bg-warning-600 text-white px-4 py-2 text-center text-sm font-medium"
    >
      <i class="lucide-wifi-off mr-2"></i>
      You are currently offline. Some features may not be available.
    </div>
    
    <!-- Main app content -->
    <div class="flex flex-col min-h-screen">
      <!-- Router view with transition -->
      <router-view 
        v-slot="{ Component }"
        class="flex-1"
      >
        <transition
          name="page"
          mode="out-in"
          @before-enter="uiStore.setPageTransition(true)"
          @after-enter="uiStore.setPageTransition(false)"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
    
    <!-- Global modals -->
    <Teleport to="body">
      <!-- Confirmation modal -->
      <div 
        v-if="uiStore.confirmationModal.isOpen"
        class="modal-overlay"
        @click.self="uiStore.closeConfirmationModal"
      >
        <div class="modal animate-slide-up">
          <div class="modal-header">
            <h3 class="text-lg font-medium text-gray-900">
              {{ uiStore.confirmationModal.title }}
            </h3>
            <button
              @click="uiStore.closeConfirmationModal"
              class="text-gray-400 hover:text-gray-600"
            >
              <i class="lucide-x w-5 h-5"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <p class="text-sm text-gray-600">
              {{ uiStore.confirmationModal.message }}
            </p>
          </div>
          
          <div class="modal-footer">
            <button
              @click="uiStore.closeConfirmationModal"
              class="btn btn-outline mr-2"
            >
              Cancel
            </button>
            <button
              @click="uiStore.confirmAction"
              class="btn btn-primary"
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
      
      <!-- Alert modal -->
      <div 
        v-if="uiStore.alertModal.isOpen"
        class="modal-overlay"
        @click.self="uiStore.closeAlertModal"
      >
        <div class="modal animate-slide-up">
          <div class="modal-header">
            <h3 class="text-lg font-medium text-gray-900">
              {{ uiStore.alertModal.title }}
            </h3>
            <button
              @click="uiStore.closeAlertModal"
              class="text-gray-400 hover:text-gray-600"
            >
              <i class="lucide-x w-5 h-5"></i>
            </button>
          </div>
          
          <div class="modal-body">
            <p class="text-sm text-gray-600">
              {{ uiStore.alertModal.message }}
            </p>
          </div>
          
          <div class="modal-footer">
            <button
              @click="uiStore.closeAlertModal"
              class="btn btn-primary"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* Page transition styles */
.page-enter-active, .page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

/* Custom toast styles */
:global(.custom-toast) {
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

:global(.custom-toast-body) {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

:global(.custom-toast-container) {
  z-index: 9999;
}

/* Loading spinner animation */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.spinner {
  animation: spin 1s linear infinite;
}
</style>