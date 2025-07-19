import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate'
import Toast from 'vue-toastification'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'
import './assets/css/main.css'

// Import toast styles
import 'vue-toastification/dist/index.css'

// Import i18n messages
import en from './locales/en.json'
import es from './locales/es.json'

// Create Vue app
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()
pinia.use(createPersistedState({
  storage: localStorage,
  key: 'cwv-store',
}))

// Create i18n instance
const i18n = createI18n({
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en,
    es,
  },
})

// Toast configuration
const toastOptions = {
  position: 'top-right' as const,
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
  maxToasts: 5,
  newestOnTop: true,
  transition: 'Vue-Toastification__bounce',
  toastClassName: 'custom-toast',
  bodyClassName: 'custom-toast-body',
  containerClassName: 'custom-toast-container',
  filterBeforeCreate: (toast: any, toasts: any[]) => {
    // Prevent duplicate toasts
    if (toasts.filter(t => t.content === toast.content).length !== 0) {
      return false
    }
    return toast
  },
}

// Register plugins
app.use(pinia)
app.use(router)
app.use(i18n)
app.use(Toast, toastOptions)

// Global error handler
app.config.errorHandler = (error: Error, instance, info) => {
  console.error('Global error handler:', error)
  console.error('Component instance:', instance)
  console.error('Error info:', info)
  
  // In production, you might want to send this to an error reporting service
  if (import.meta.env.PROD) {
    // Send to error reporting service (e.g., Sentry)
    // Sentry.captureException(error, { extra: { info } })
  }
}

// Global warning handler
app.config.warnHandler = (msg, instance, trace) => {
  console.warn('Global warning handler:', msg)
  console.warn('Component instance:', instance)
  console.warn('Trace:', trace)
}

// Performance monitoring
if (import.meta.env.DEV) {
  app.config.performance = true
}

// Initialize theme before mounting
// The theme will be initialized when useTheme is first called
// But we need to ensure it happens before the app renders
import('./composables/useTheme').then(({ useTheme }) => {
  useTheme() // This will trigger initialization
})

// Mount the app
app.mount('#app')

// Hide loading spinner
const loadingSpinner = document.getElementById('loading-spinner')
if (loadingSpinner) {
  loadingSpinner.classList.add('fade-out')
  setTimeout(() => {
    loadingSpinner.remove()
  }, 300)
}

// Service worker registration for PWA
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration)
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError)
      })
  })
}

// Export app instance for debugging in development
if (import.meta.env.DEV) {
  (window as any).app = app
}