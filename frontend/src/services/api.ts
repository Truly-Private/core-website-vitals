import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const authStore = useAuthStore()
    const uiStore = useUIStore()
    
    // Skip auth for trial endpoints
    const isTrialEndpoint = config.url?.includes('/analyses/trial')
    
    // Add auth token if available and not a trial endpoint
    if (authStore.accessToken && !isTrialEndpoint) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${authStore.accessToken}`,
      }
    }
    
    // Add request ID for debugging
    config.headers = {
      ...config.headers,
      'X-Request-ID': `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    }
    
    // Note: User-Agent cannot be set in browser environments due to security restrictions
    
    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Token refresh promise to prevent multiple simultaneous refresh attempts
let refreshTokenPromise: Promise<boolean> | null = null

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`API Success: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
    }
    
    return response
  },
  async (error) => {
    const authStore = useAuthStore()
    const uiStore = useUIStore()
    
    // Log errors in development
    if (import.meta.env.DEV) {
      console.error('API Error:', error)
    }
    
    // Handle network errors
    if (!error.response) {
      uiStore.showErrorNotification(
        'Network Error',
        'Unable to connect to the server. Please check your internet connection.'
      )
      return Promise.reject(new Error('Network error'))
    }
    
    const { status, data } = error.response
    
    // Handle specific error codes
    switch (status) {
      case 401:
        // Skip auth handling for trial endpoints
        const isTrialEndpoint = error.config?.url?.includes('/analyses/trial')
        if (isTrialEndpoint) {
          return Promise.reject(error)
        }
        
        // Skip refresh attempt if this was already a refresh request
        if (error.config?.url?.includes('/auth/refresh')) {
          return Promise.reject(error)
        }
        
        // Unauthorized - try to refresh token
        if (authStore.refreshToken) {
          try {
            // If a refresh is already in progress, wait for it
            if (refreshTokenPromise) {
              const refreshed = await refreshTokenPromise
              if (refreshed) {
                // Update the request with the new token
                error.config.headers['Authorization'] = `Bearer ${authStore.accessToken}`
                return apiClient.request(error.config)
              }
            } else {
              // Start a new refresh
              refreshTokenPromise = authStore.refreshAccessToken()
              const refreshed = await refreshTokenPromise
              refreshTokenPromise = null
              
              if (refreshed) {
                // Update the request with the new token
                error.config.headers['Authorization'] = `Bearer ${authStore.accessToken}`
                return apiClient.request(error.config)
              }
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            refreshTokenPromise = null
          }
        }
        
        // Redirect to login
        authStore.clearAuthState()
        window.location.href = '/login'
        return Promise.reject(new Error('Authentication failed'))
        
      case 403:
        uiStore.showErrorNotification(
          'Access Denied',
          'You do not have permission to perform this action.'
        )
        break
        
      case 404:
        uiStore.showErrorNotification(
          'Not Found',
          'The requested resource was not found.'
        )
        break
        
      case 422:
        // Validation errors
        if (data && data.detail) {
          const errorMessage = Array.isArray(data.detail)
            ? data.detail.map((err: any) => err.msg).join(', ')
            : data.detail
          uiStore.showErrorNotification('Validation Error', errorMessage)
        }
        break
        
      case 429:
        uiStore.showErrorNotification(
          'Too Many Requests',
          'You have exceeded the rate limit. Please try again later.'
        )
        break
        
      case 500:
        uiStore.showErrorNotification(
          'Server Error',
          'An internal server error occurred. Please try again later.'
        )
        break
        
      case 502:
      case 503:
      case 504:
        uiStore.showErrorNotification(
          'Service Unavailable',
          'The service is temporarily unavailable. Please try again later.'
        )
        break
        
      default:
        uiStore.showErrorNotification(
          'Error',
          data?.message || 'An unexpected error occurred.'
        )
    }
    
    return Promise.reject(error)
  }
)

// API service methods
export const apiService = {
  // Generic HTTP methods
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.get(url, config)
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.post(url, data, config)
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.put(url, data, config)
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.patch(url, data, config)
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.delete(url, config)
  },
  
  // File upload
  uploadFile: (url: string, file: File, onUploadProgress?: (progress: number) => void): Promise<AxiosResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    
    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(progress)
        }
      },
    })
  },
  
  // Download file
  downloadFile: async (url: string, filename?: string): Promise<void> => {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  },
  
  // Health check
  healthCheck: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get('/health')
      return response.status === 200
    } catch (error) {
      return false
    }
  },
  
  // Cancel request
  cancelRequest: (cancelToken: any) => {
    return axios.CancelToken.source()
  },
}

// Specific API endpoints
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    apiService.post('/auth/login', credentials),
    
  register: (userData: { email: string; password: string; full_name: string }) =>
    apiService.post('/auth/register', userData),
    
  logout: () =>
    apiService.post('/auth/logout'),
    
  refreshToken: (refreshToken: string) =>
    apiService.post('/auth/refresh', { refresh_token: refreshToken }),
    
  forgotPassword: (email: string) =>
    apiService.post('/auth/forgot-password', { email }),
    
  resetPassword: (token: string, password: string) =>
    apiService.post('/auth/reset-password', { token, password }),
    
  verifyEmail: (token: string) =>
    apiService.post('/auth/verify-email', { token }),
}

export const userAPI = {
  getProfile: () =>
    apiService.get('/users/me/profile'),
    
  updateProfile: (profileData: any) =>
    apiService.put('/users/me', profileData),
    
  changePassword: (currentPassword: string, newPassword: string) =>
    apiService.post('/users/me/change-password', { current_password: currentPassword, new_password: newPassword }),
    
  deleteAccount: (password: string) =>
    apiService.delete('/users/me', { data: { password } }),
    
  getUsageStats: () =>
    apiService.get('/users/me/usage'),
    
  updateSettings: (settings: any) =>
    apiService.put('/users/me/settings', settings),
}

export const analysisAPI = {
  submitAnalysis: (analysisData: any) =>
    apiService.post('/analyses', analysisData),
    
  getAnalyses: (params?: any) =>
    apiService.get('/analyses', { params }),
    
  getAnalysisById: (id: string) =>
    apiService.get(`/analyses/${id}`),
    
  updateAnalysis: (id: string, updateData: any) =>
    apiService.put(`/analyses/${id}`, updateData),
    
  deleteAnalysis: (id: string) =>
    apiService.delete(`/analyses/${id}`),
    
  getAnalysisStatus: (id: string) =>
    apiService.get(`/analyses/${id}/status`),
    
  retryAnalysis: (id: string) =>
    apiService.post(`/analyses/${id}/retry`),
    
  submitBatchAnalysis: (urls: string[], analysisType: string) =>
    apiService.post('/analyses/batch', { urls, analysis_type: analysisType }),
    
  exportAnalysis: (id: string, format: string) =>
    apiService.get(`/analyses/${id}/export?format=${format}`, { responseType: 'blob' }),
}

export const dashboardAPI = {
  getSummary: () =>
    apiService.get('/dashboard/summary'),
    
  getTrends: (period?: string) =>
    apiService.get('/dashboard/trends', { params: { period } }),
    
  getRecentActivity: () =>
    apiService.get('/dashboard/recent-activity'),
    
  getAnalyticsData: (dateRange?: { start: string; end: string }) =>
    apiService.get('/dashboard/analytics', { params: dateRange }),
}

// Export the axios instance for direct use if needed
export { apiClient }
export default apiService