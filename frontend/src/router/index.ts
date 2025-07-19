import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

// Lazy-loaded page components
const HomeView = () => import('@/views/HomeView.vue')
const LoginView = () => import('@/views/auth/LoginView.vue')
const RegisterView = () => import('@/views/auth/RegisterView.vue')
const ForgotPasswordView = () => import('@/views/auth/ForgotPasswordView.vue')
const ResetPasswordView = () => import('@/views/auth/ResetPasswordView.vue')
const DashboardView = () => import('@/views/DashboardView.vue')
const AnalysisView = () => import('@/views/analysis/AnalysisView.vue')
const AnalysisResultView = () => import('@/views/analysis/AnalysisResultView.vue')
const AnalysisHistoryView = () => import('@/views/analysis/AnalysisHistoryView.vue')
const ProfileView = () => import('@/views/ProfileView.vue')
const SettingsView = () => import('@/views/SettingsView.vue')
const BillingView = () => import('@/views/BillingView.vue')
const NotFoundView = () => import('@/views/NotFoundView.vue')
const TrialAnalysisView = () => import('@/views/TrialAnalysisView.vue')
const TrialResultsView = () => import('@/views/TrialResultsView.vue')

// Define routes
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: 'Home',
      description: 'Core Website Vitals - SEO Analysis Platform',
      requiresAuth: false,
    },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      title: 'Login',
      description: 'Sign in to your Core Website Vitals account',
      requiresAuth: false,
      hideForAuthenticated: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: {
      title: 'Register',
      description: 'Create a new Core Website Vitals account',
      requiresAuth: false,
      hideForAuthenticated: true,
    },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: ForgotPasswordView,
    meta: {
      title: 'Forgot Password',
      description: 'Reset your Core Website Vitals password',
      requiresAuth: false,
      hideForAuthenticated: true,
    },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: ResetPasswordView,
    meta: {
      title: 'Reset Password',
      description: 'Set a new password for your account',
      requiresAuth: false,
      hideForAuthenticated: true,
    },
  },
  {
    path: '/try',
    name: 'trial',
    component: TrialAnalysisView,
    meta: {
      title: 'Try Core Website Vitals Free',
      description: 'Get a free SEO analysis of your website - no sign up required',
      requiresAuth: false,
    },
  },
  {
    path: '/try/results/:id',
    name: 'trial-results',
    component: TrialResultsView,
    meta: {
      title: 'Trial Analysis Results',
      description: 'Your free SEO analysis results',
      requiresAuth: false,
    },
    props: true,
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: {
      title: 'Dashboard',
      description: 'Your SEO analysis dashboard',
      requiresAuth: true,
    },
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: AnalysisView,
    meta: {
      title: 'New Analysis',
      description: 'Start a new SEO analysis',
      requiresAuth: true,
    },
  },
  {
    path: '/analysis/:id',
    name: 'analysis-result',
    component: AnalysisResultView,
    meta: {
      title: 'Analysis Result',
      description: 'View SEO analysis results',
      requiresAuth: true,
    },
    props: true,
  },
  {
    path: '/history',
    name: 'analysis-history',
    component: AnalysisHistoryView,
    meta: {
      title: 'Analysis History',
      description: 'View your past SEO analyses',
      requiresAuth: true,
    },
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfileView,
    meta: {
      title: 'Profile',
      description: 'Manage your account profile',
      requiresAuth: true,
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: {
      title: 'Settings',
      description: 'Account settings and preferences',
      requiresAuth: true,
    },
  },
  {
    path: '/billing',
    name: 'billing',
    component: BillingView,
    meta: {
      title: 'Billing',
      description: 'Manage your subscription and billing',
      requiresAuth: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
    meta: {
      title: 'Page Not Found',
      description: 'The page you are looking for does not exist',
      requiresAuth: false,
    },
  },
]

// Create router instance
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Handle scroll behavior on route change
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0, behavior: 'smooth' }
    }
  },
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const uiStore = useUIStore()
  
  // Show loading indicator
  uiStore.setLoading(true, 'Loading page...')
  
  // Initialize auth if not already done
  if (!authStore.isInitialized) {
    await authStore.initializeAuth()
  }
  
  // Check authentication requirements
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login with return URL
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    })
    return
  }
  
  // Hide auth pages for authenticated users
  if (to.meta.hideForAuthenticated && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
    return
  }
  
  // Check subscription requirements (if any)
  if (to.meta.requiresSubscription && !authStore.hasActiveSubscription) {
    next({ name: 'billing' })
    return
  }
  
  // Proceed with navigation
  next()
})

router.beforeResolve(async (to, from, next) => {
  // This runs after all async components have been resolved
  // but before the route is confirmed
  
  // Update page meta tags
  if (to.meta.title) {
    document.title = `${to.meta.title} - Core Website Vitals`
  }
  
  if (to.meta.description) {
    const metaDescription = document.querySelector('meta[name="description"]')
    if (metaDescription) {
      metaDescription.setAttribute('content', to.meta.description)
    }
  }
  
  next()
})

router.afterEach((to, from) => {
  const uiStore = useUIStore()
  
  // Hide loading indicator
  uiStore.setLoading(false)
  
  // Track page view for analytics
  if (import.meta.env.PROD && window.gtag) {
    window.gtag('config', 'GA_MEASUREMENT_ID', {
      page_title: to.meta.title,
      page_location: window.location.href,
      page_path: to.path,
    })
  }
  
  // Clear any error states
  uiStore.clearErrors()
})

// Handle navigation errors
router.onError((error) => {
  console.error('Router error:', error)
  
  const uiStore = useUIStore()
  uiStore.setLoading(false)
  
  // Show error toast
  if (error.message.includes('Loading chunk')) {
    // Handle chunk loading errors (usually due to new deployment)
    uiStore.showAlert(
      'Update Available',
      'A new version is available. Please refresh the page to continue.'
    )
  } else {
    uiStore.showAlert(
      'Navigation Error',
      'Failed to load the page. Please try again.'
    )
  }
})

export default router

// Export route names for type safety
export const routeNames = {
  home: 'home',
  login: 'login',
  register: 'register',
  forgotPassword: 'forgot-password',
  resetPassword: 'reset-password',
  trial: 'trial',
  trialResults: 'trial-results',
  dashboard: 'dashboard',
  analysis: 'analysis',
  analysisResult: 'analysis-result',
  analysisHistory: 'analysis-history',
  profile: 'profile',
  settings: 'settings',
  billing: 'billing',
  notFound: 'not-found',
} as const

// Export route types
export type RouteNames = typeof routeNames[keyof typeof routeNames]

// Custom router composable
export const useAppRouter = () => {
  return {
    router,
    routeNames,
    // Helper function to navigate with type safety
    navigateTo: (name: RouteNames, params?: any, query?: any) => {
      return router.push({ name, params, query })
    },
    // Helper function to replace current route
    replaceTo: (name: RouteNames, params?: any, query?: any) => {
      return router.replace({ name, params, query })
    },
    // Helper function to go back
    goBack: () => {
      return router.back()
    },
    // Helper function to go forward
    goForward: () => {
      return router.forward()
    },
  }
}