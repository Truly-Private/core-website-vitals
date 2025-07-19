import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'
import { supabase } from '@/services/supabase'
import type { 
  AnalysisTask, 
  AnalysisStatus, 
  AnalysisType, 
  AnalysisResults,
  AnalysisSubmission,
  AnalysisFilters,
  PaginatedAnalyses
} from '@/types/analysis.types'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const analyses = ref<AnalysisTask[]>([])
  const currentAnalysis = ref<AnalysisTask | null>(null)
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const error = ref<string | null>(null)
  const filters = ref<AnalysisFilters>({
    status: null,
    analysisType: null,
    dateRange: null,
    page: 1,
    pageSize: 10,
  })
  const totalCount = ref(0)
  const hasMore = ref(true)
  
  // Real-time subscription
  const subscription = ref<any>(null)
  
  // Getters
  const pendingAnalyses = computed(() => 
    analyses.value.filter(a => a.status === 'PENDING')
  )
  
  const inProgressAnalyses = computed(() => 
    analyses.value.filter(a => a.status === 'IN_PROGRESS')
  )
  
  const completedAnalyses = computed(() => 
    analyses.value.filter(a => a.status === 'SUCCESS')
  )
  
  const failedAnalyses = computed(() => 
    analyses.value.filter(a => a.status === 'FAILED')
  )
  
  const recentAnalyses = computed(() => 
    analyses.value
      .slice()
      .sort((a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime())
      .slice(0, 10)
  )
  
  const analysisStats = computed(() => ({
    total: analyses.value.length,
    pending: pendingAnalyses.value.length,
    inProgress: inProgressAnalyses.value.length,
    completed: completedAnalyses.value.length,
    failed: failedAnalyses.value.length,
    successRate: analyses.value.length > 0 
      ? (completedAnalyses.value.length / analyses.value.length) * 100 
      : 0,
  }))
  
  const isAnalysisInProgress = computed(() => 
    inProgressAnalyses.value.length > 0 || pendingAnalyses.value.length > 0
  )
  
  // Actions
  const fetchAnalyses = async (resetList = false) => {
    if (resetList) {
      analyses.value = []
      filters.value.page = 1
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      const params = new URLSearchParams()
      params.append('page', filters.value.page.toString())
      params.append('page_size', filters.value.pageSize.toString())
      
      if (filters.value.status) {
        params.append('status', filters.value.status)
      }
      
      if (filters.value.analysisType) {
        params.append('analysis_type', filters.value.analysisType)
      }
      
      const response = await apiClient.get<PaginatedAnalyses>(`/analyses?${params}`)
      
      if (response.data) {
        const { items, total, page, pages } = response.data
        
        if (resetList) {
          analyses.value = items
        } else {
          analyses.value = [...analyses.value, ...items]
        }
        
        totalCount.value = total
        hasMore.value = page < pages
        
        return response.data
      }
    } catch (err) {
      console.error('Failed to fetch analyses:', err)
      error.value = err instanceof Error ? err.message : 'Failed to fetch analyses'
    } finally {
      isLoading.value = false
    }
  }
  
  const fetchAnalysisById = async (id: string): Promise<AnalysisTask | null> => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get<AnalysisTask>(`/analyses/${id}`)
      
      if (response.data) {
        currentAnalysis.value = response.data
        
        // Update in analyses list if exists
        const index = analyses.value.findIndex(a => a.id === id)
        if (index > -1) {
          analyses.value[index] = response.data
        }
        
        return response.data
      }
      
      return null
    } catch (err) {
      console.error('Failed to fetch analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to fetch analysis'
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  const submitAnalysis = async (submission: AnalysisSubmission): Promise<AnalysisTask | null> => {
    isSubmitting.value = true
    error.value = null
    
    try {
      const response = await apiClient.post<AnalysisTask>('/analyses', submission)
      
      if (response.data) {
        analyses.value.unshift(response.data)
        currentAnalysis.value = response.data
        
        return response.data
      }
      
      return null
    } catch (err) {
      console.error('Failed to submit analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to submit analysis'
      return null
    } finally {
      isSubmitting.value = false
    }
  }
  
  const submitBatchAnalysis = async (urls: string[], analysisType: AnalysisType = 'full_seo'): Promise<AnalysisTask[] | null> => {
    isSubmitting.value = true
    error.value = null
    
    try {
      const response = await apiClient.post<AnalysisTask[]>('/analyses/batch', {
        urls,
        analysis_type: analysisType,
      })
      
      if (response.data) {
        analyses.value.unshift(...response.data)
        
        return response.data
      }
      
      return null
    } catch (err) {
      console.error('Failed to submit batch analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to submit batch analysis'
      return null
    } finally {
      isSubmitting.value = false
    }
  }
  
  const cancelAnalysis = async (id: string): Promise<boolean> => {
    try {
      const response = await apiClient.put<AnalysisTask>(`/analyses/${id}`, {
        status: 'CANCELLED',
      })
      
      if (response.data) {
        const index = analyses.value.findIndex(a => a.id === id)
        if (index > -1) {
          analyses.value[index] = response.data
        }
        
        if (currentAnalysis.value?.id === id) {
          currentAnalysis.value = response.data
        }
        
        return true
      }
      
      return false
    } catch (err) {
      console.error('Failed to cancel analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to cancel analysis'
      return false
    }
  }
  
  const retryAnalysis = async (id: string): Promise<boolean> => {
    try {
      const response = await apiClient.post<AnalysisTask>(`/analyses/${id}/retry`)
      
      if (response.data) {
        const index = analyses.value.findIndex(a => a.id === id)
        if (index > -1) {
          analyses.value[index] = response.data
        }
        
        if (currentAnalysis.value?.id === id) {
          currentAnalysis.value = response.data
        }
        
        return true
      }
      
      return false
    } catch (err) {
      console.error('Failed to retry analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to retry analysis'
      return false
    }
  }
  
  const deleteAnalysis = async (id: string): Promise<boolean> => {
    try {
      await apiClient.delete(`/analyses/${id}`)
      
      analyses.value = analyses.value.filter(a => a.id !== id)
      
      if (currentAnalysis.value?.id === id) {
        currentAnalysis.value = null
      }
      
      return true
    } catch (err) {
      console.error('Failed to delete analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to delete analysis'
      return false
    }
  }
  
  const getAnalysisStatus = async (id: string): Promise<any> => {
    try {
      const response = await apiClient.get(`/analyses/${id}/status`)
      return response.data
    } catch (err) {
      console.error('Failed to get analysis status:', err)
      return null
    }
  }
  
  const setFilters = (newFilters: Partial<AnalysisFilters>) => {
    filters.value = { ...filters.value, ...newFilters }
  }
  
  const resetFilters = () => {
    filters.value = {
      status: null,
      analysisType: null,
      dateRange: null,
      page: 1,
      pageSize: 10,
    }
  }
  
  const loadMore = async () => {
    if (hasMore.value && !isLoading.value) {
      filters.value.page++
      await fetchAnalyses(false)
    }
  }
  
  const refreshAnalyses = async () => {
    await fetchAnalyses(true)
  }
  
  const subscribeToRealTimeUpdates = (userId: string) => {
    // Unsubscribe from existing subscription
    if (subscription.value) {
      subscription.value.unsubscribe()
    }
    
    // Subscribe to analysis task updates
    subscription.value = supabase
      .channel('analysis_tasks')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'analysis_tasks',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          handleRealtimeUpdate(payload)
        }
      )
      .subscribe()
  }
  
  const unsubscribeFromRealTimeUpdates = () => {
    if (subscription.value) {
      subscription.value.unsubscribe()
      subscription.value = null
    }
  }
  
  const handleRealtimeUpdate = (payload: any) => {
    const { eventType, new: newRecord, old: oldRecord } = payload
    
    switch (eventType) {
      case 'INSERT':
        if (newRecord) {
          const existingIndex = analyses.value.findIndex(a => a.id === newRecord.id)
          if (existingIndex === -1) {
            analyses.value.unshift(newRecord as AnalysisTask)
          }
        }
        break
        
      case 'UPDATE':
        if (newRecord) {
          const index = analyses.value.findIndex(a => a.id === newRecord.id)
          if (index > -1) {
            analyses.value[index] = newRecord as AnalysisTask
          }
          
          if (currentAnalysis.value?.id === newRecord.id) {
            currentAnalysis.value = newRecord as AnalysisTask
          }
        }
        break
        
      case 'DELETE':
        if (oldRecord) {
          analyses.value = analyses.value.filter(a => a.id !== oldRecord.id)
          
          if (currentAnalysis.value?.id === oldRecord.id) {
            currentAnalysis.value = null
          }
        }
        break
    }
  }
  
  const clearError = () => {
    error.value = null
  }
  
  const clearCurrentAnalysis = () => {
    currentAnalysis.value = null
  }
  
  const clearAnalyses = () => {
    analyses.value = []
    currentAnalysis.value = null
    totalCount.value = 0
    hasMore.value = true
  }

  // Real-time update methods
  const updateAnalysisFromRealtime = (data: any) => {
    // Handle real-time updates from WebSocket
    if (data.analysis_id) {
      const index = analyses.value.findIndex(a => a.id === data.analysis_id)
      if (index !== -1) {
        analyses.value[index] = { ...analyses.value[index], ...data }
      }
    }
  }

  const updateAnalysisProgress = (analysisId: string, progress: any) => {
    const index = analyses.value.findIndex(a => a.id === analysisId)
    if (index !== -1) {
      analyses.value[index] = { ...analyses.value[index], progress }
    }
  }

  const addAnalysisTask = (task: AnalysisTask) => {
    const existingIndex = analyses.value.findIndex(a => a.id === task.id)
    if (existingIndex === -1) {
      analyses.value.unshift(task)
    }
  }

  const updateAnalysisTask = (task: AnalysisTask) => {
    const index = analyses.value.findIndex(a => a.id === task.id)
    if (index !== -1) {
      analyses.value[index] = task
    }
  }

  const removeAnalysisTask = (taskId: string) => {
    const index = analyses.value.findIndex(a => a.id === taskId)
    if (index !== -1) {
      analyses.value.splice(index, 1)
    }
  }

  const deleteAnalyses = async (analysisIds: string[]): Promise<boolean> => {
    try {
      await apiClient.post('/analyses/batch-delete', { ids: analysisIds })
      
      analyses.value = analyses.value.filter(a => !analysisIds.includes(a.id))
      
      if (currentAnalysis.value && analysisIds.includes(currentAnalysis.value.id)) {
        currentAnalysis.value = null
      }
      
      return true
    } catch (err) {
      console.error('Failed to delete analyses:', err)
      error.value = err instanceof Error ? err.message : 'Failed to delete analyses'
      return false
    }
  }

  const exportAnalysis = async (analysisId: string, format: string): Promise<Blob> => {
    try {
      const response = await apiClient.get(`/analyses/${analysisId}/export`, {
        params: { format },
        responseType: 'blob'
      })
      
      return response.data
    } catch (err) {
      console.error('Failed to export analysis:', err)
      error.value = err instanceof Error ? err.message : 'Failed to export analysis'
      throw err
    }
  }
  
  // Utility functions
  const getStatusColor = (status: AnalysisStatus): string => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800'
      case 'IN_PROGRESS':
        return 'bg-blue-100 text-blue-800'
      case 'SUCCESS':
        return 'bg-green-100 text-green-800'
      case 'FAILED':
        return 'bg-red-100 text-red-800'
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }
  
  const getStatusIcon = (status: AnalysisStatus): string => {
    switch (status) {
      case 'PENDING':
        return 'clock'
      case 'IN_PROGRESS':
        return 'loader'
      case 'SUCCESS':
        return 'check-circle'
      case 'FAILED':
        return 'x-circle'
      case 'CANCELLED':
        return 'ban'
      default:
        return 'help-circle'
    }
  }
  
  const formatAnalysisType = (type: AnalysisType): string => {
    switch (type) {
      case 'full_seo':
        return 'Full SEO Analysis'
      case 'technical_seo':
        return 'Technical SEO'
      case 'content_analysis':
        return 'Content Analysis'
      case 'performance_audit':
        return 'Performance Audit'
      default:
        return type
    }
  }
  
  const calculateDuration = (startTime: string, endTime?: string): string => {
    const start = new Date(startTime).getTime()
    const end = endTime ? new Date(endTime).getTime() : Date.now()
    const duration = Math.floor((end - start) / 1000)
    
    if (duration < 60) {
      return `${duration}s`
    } else if (duration < 3600) {
      return `${Math.floor(duration / 60)}m ${duration % 60}s`
    } else {
      const hours = Math.floor(duration / 3600)
      const minutes = Math.floor((duration % 3600) / 60)
      return `${hours}h ${minutes}m`
    }
  }
  
  return {
    // State
    analyses: readonly(analyses),
    currentAnalysis: readonly(currentAnalysis),
    isLoading: readonly(isLoading),
    isSubmitting: readonly(isSubmitting),
    error: readonly(error),
    filters: readonly(filters),
    totalCount: readonly(totalCount),
    hasMore: readonly(hasMore),
    
    // Getters
    pendingAnalyses,
    inProgressAnalyses,
    completedAnalyses,
    failedAnalyses,
    recentAnalyses,
    analysisStats,
    isAnalysisInProgress,
    
    // Actions
    fetchAnalyses,
    fetchAnalysisById,
    submitAnalysis,
    submitBatchAnalysis,
    cancelAnalysis,
    retryAnalysis,
    deleteAnalysis,
    deleteAnalyses,
    exportAnalysis,
    getAnalysisStatus,
    setFilters,
    resetFilters,
    loadMore,
    refreshAnalyses,
    subscribeToRealTimeUpdates,
    unsubscribeFromRealTimeUpdates,
    clearError,
    clearCurrentAnalysis,
    clearAnalyses,
    
    // Real-time methods
    updateAnalysisFromRealtime,
    updateAnalysisProgress,
    addAnalysisTask,
    updateAnalysisTask,
    removeAnalysisTask,
    
    // Utilities
    getStatusColor,
    getStatusIcon,
    formatAnalysisType,
    calculateDuration,
  }
})