import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

export interface ConfirmationModal {
  isOpen: boolean
  title: string
  message: string
  onConfirm: () => void
  onCancel?: () => void
}

export interface AlertModal {
  isOpen: boolean
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  duration?: number
  action?: {
    label: string
    handler: () => void
  }
}

export const useUIStore = defineStore('ui', () => {
  // State
  const theme = ref<Theme>('system')
  const sidebarOpen = ref(false)
  const isLoading = ref(false)
  const loadingMessage = ref('')
  const isOnline = ref(navigator.onLine)
  const hasUnsavedChanges = ref(false)
  const pageTransition = ref(false)
  const errors = ref<string[]>([])
  const notifications = ref<Notification[]>([])
  
  // Modal state
  const confirmationModal = ref<ConfirmationModal>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
    onCancel: undefined,
  })
  
  const alertModal = ref<AlertModal>({
    isOpen: false,
    title: '',
    message: '',
    type: 'info',
  })
  
  // Getters
  const isDarkMode = computed(() => {
    if (theme.value === 'dark') return true
    if (theme.value === 'light') return false
    // For system theme, check preference but default to dark
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return false
    }
    return true // Default to dark mode
  })
  
  const hasErrors = computed(() => errors.value.length > 0)
  
  const unreadNotifications = computed(() => 
    notifications.value.filter(n => !n.action?.label.includes('read'))
  )
  
  // Actions
  const initializeTheme = () => {
    // Load theme from localStorage or detect system preference
    const savedTheme = localStorage.getItem('cwv-theme') as Theme
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      theme.value = savedTheme
    } else {
      // Default to dark mode instead of system
      theme.value = 'dark'
    }
    
    // Apply theme
    applyTheme()
    
    // Watch for system theme changes
    if (theme.value === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addListener(applyTheme)
    }
  }
  
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('cwv-theme', newTheme)
    applyTheme()
  }
  
  const applyTheme = () => {
    const root = document.documentElement
    const shouldBeDark = isDarkMode.value
    
    if (shouldBeDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    
    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', shouldBeDark ? '#1f2937' : '#3b82f6')
    }
  }
  
  const toggleSidebar = () => {
    sidebarOpen.value = !sidebarOpen.value
  }
  
  const setSidebarOpen = (isOpen: boolean) => {
    sidebarOpen.value = isOpen
  }
  
  const setLoading = (loading: boolean, message = '') => {
    isLoading.value = loading
    loadingMessage.value = message
  }
  
  const setOnlineStatus = (online: boolean) => {
    isOnline.value = online
  }
  
  const setUnsavedChanges = (hasChanges: boolean) => {
    hasUnsavedChanges.value = hasChanges
  }
  
  const setPageTransition = (inTransition: boolean) => {
    pageTransition.value = inTransition
  }
  
  const addError = (error: string) => {
    if (!errors.value.includes(error)) {
      errors.value.push(error)
    }
  }
  
  const removeError = (error: string) => {
    const index = errors.value.indexOf(error)
    if (index > -1) {
      errors.value.splice(index, 1)
    }
  }
  
  const clearErrors = () => {
    errors.value = []
  }
  
  const showConfirmation = (
    title: string,
    message: string,
    onConfirm: () => void,
    onCancel?: () => void
  ) => {
    confirmationModal.value = {
      isOpen: true,
      title,
      message,
      onConfirm,
      onCancel,
    }
  }
  
  const closeConfirmationModal = () => {
    if (confirmationModal.value.onCancel) {
      confirmationModal.value.onCancel()
    }
    confirmationModal.value.isOpen = false
  }
  
  const confirmAction = () => {
    confirmationModal.value.onConfirm()
    confirmationModal.value.isOpen = false
  }
  
  const showAlert = (
    title: string,
    message: string,
    type: AlertModal['type'] = 'info'
  ) => {
    alertModal.value = {
      isOpen: true,
      title,
      message,
      type,
    }
  }
  
  const closeAlertModal = () => {
    alertModal.value.isOpen = false
  }
  
  const addNotification = (notification: Omit<Notification, 'id'>) => {
    const id = Date.now().toString()
    const newNotification: Notification = {
      id,
      ...notification,
    }
    
    notifications.value.unshift(newNotification)
    
    // Auto-remove notification after duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration)
    }
    
    return id
  }
  
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  const clearNotifications = () => {
    notifications.value = []
  }
  
  const showSuccessNotification = (title: string, message: string, duration = 5000) => {
    return addNotification({
      type: 'success',
      title,
      message,
      duration,
    })
  }
  
  const showErrorNotification = (title: string, message: string, duration = 0) => {
    return addNotification({
      type: 'error',
      title,
      message,
      duration,
    })
  }
  
  const showWarningNotification = (title: string, message: string, duration = 7000) => {
    return addNotification({
      type: 'warning',
      title,
      message,
      duration,
    })
  }
  
  const showInfoNotification = (title: string, message: string, duration = 5000) => {
    return addNotification({
      type: 'info',
      title,
      message,
      duration,
    })
  }

  const showNotification = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info', duration?: number) => {
    return addNotification({
      type,
      title: type.charAt(0).toUpperCase() + type.slice(1),
      message,
      duration: duration || (type === 'error' ? 0 : 5000),
    })
  }

  const showConfirmDialog = (
    title: string,
    message: string,
    confirmText = 'Confirm',
    variant: 'default' | 'danger' = 'default'
  ): Promise<boolean> => {
    return new Promise((resolve) => {
      confirmationModal.value = {
        isOpen: true,
        title,
        message,
        onConfirm: () => {
          confirmationModal.value.isOpen = false
          resolve(true)
        },
        onCancel: () => {
          confirmationModal.value.isOpen = false
          resolve(false)
        },
      }
    })
  }
  
  // Keyboard shortcuts
  const handleKeyboardShortcut = (event: KeyboardEvent) => {
    // Ctrl/Cmd + K for search
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
      event.preventDefault()
      // Implement search functionality
    }
    
    // Ctrl/Cmd + B for sidebar toggle
    if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
      event.preventDefault()
      toggleSidebar()
    }
    
    // Ctrl/Cmd + D for theme toggle
    if ((event.ctrlKey || event.metaKey) && event.key === 'd') {
      event.preventDefault()
      setTheme(theme.value === 'dark' ? 'light' : 'dark')
    }
    
    // Escape key to close modals
    if (event.key === 'Escape') {
      if (confirmationModal.value.isOpen) {
        closeConfirmationModal()
      } else if (alertModal.value.isOpen) {
        closeAlertModal()
      }
    }
  }
  
  // Initialize keyboard shortcuts
  const initializeKeyboardShortcuts = () => {
    document.addEventListener('keydown', handleKeyboardShortcut)
  }
  
  const destroyKeyboardShortcuts = () => {
    document.removeEventListener('keydown', handleKeyboardShortcut)
  }
  
  // Utility functions
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const remainingSeconds = seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${remainingSeconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`
    } else {
      return `${remainingSeconds}s`
    }
  }
  
  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text)
      showSuccessNotification('Copied!', 'Text copied to clipboard')
      return true
    } catch (error) {
      showErrorNotification('Copy Failed', 'Failed to copy text to clipboard')
      return false
    }
  }
  
  const downloadFile = (content: string, filename: string, contentType = 'text/plain') => {
    const blob = new Blob([content], { type: contentType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
  
  return {
    // State
    theme: readonly(theme),
    sidebarOpen: readonly(sidebarOpen),
    isLoading: readonly(isLoading),
    loadingMessage: readonly(loadingMessage),
    isOnline: readonly(isOnline),
    hasUnsavedChanges: readonly(hasUnsavedChanges),
    pageTransition: readonly(pageTransition),
    errors: readonly(errors),
    notifications: readonly(notifications),
    confirmationModal: readonly(confirmationModal),
    alertModal: readonly(alertModal),
    
    // Getters
    isDarkMode,
    hasErrors,
    unreadNotifications,
    
    // Actions
    initializeTheme,
    setTheme,
    toggleSidebar,
    setSidebarOpen,
    setLoading,
    setOnlineStatus,
    setUnsavedChanges,
    setPageTransition,
    addError,
    removeError,
    clearErrors,
    showConfirmation,
    closeConfirmationModal,
    confirmAction,
    showAlert,
    closeAlertModal,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccessNotification,
    showErrorNotification,
    showWarningNotification,
    showInfoNotification,
    showNotification,
    showConfirmDialog,
    initializeKeyboardShortcuts,
    destroyKeyboardShortcuts,
    
    // Utilities
    formatFileSize,
    formatDuration,
    copyToClipboard,
    downloadFile,
  }
}, {
  persist: {
    storage: localStorage,
    paths: ['theme', 'sidebarOpen'],
  },
})