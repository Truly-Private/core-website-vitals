import { defineStore } from 'pinia'
import { ref, computed, readonly } from 'vue'
import { apiClient } from '@/services/api'
import type { 
  AnalysisTask, 
  AnalysisSubmission,
  AnalysisResults
} from '@/types/analysis.types'

interface TrialAnalysis extends AnalysisTask {
  isTrial: boolean
}

export const useTrialStore = defineStore('trial', () => {
  // State
  const trialAnalysis = ref<TrialAnalysis | null>(null)
  const isSubmitting = ref(false)
  const error = ref<string | null>(null)
  const hasUsedTrial = ref(false)
  
  // Check localStorage for trial usage
  const initializeTrialState = () => {
    const trialUsed = localStorage.getItem('trial_analysis_used')
    const trialData = localStorage.getItem('trial_analysis_data')
    
    if (trialUsed) {
      hasUsedTrial.value = true
    }
    
    if (trialData) {
      try {
        trialAnalysis.value = JSON.parse(trialData)
      } catch (e) {
        console.error('Failed to parse trial data:', e)
      }
    }
  }
  
  // Getters
  const canUseTrial = computed(() => !hasUsedTrial.value)
  const isTrialComplete = computed(() => 
    trialAnalysis.value?.status === 'SUCCESS' || 
    trialAnalysis.value?.status === 'FAILED'
  )
  
  // Actions
  const submitTrialAnalysis = async (url: string): Promise<TrialAnalysis | null> => {
    if (!canUseTrial.value) {
      error.value = 'Trial analysis has already been used'
      return null
    }
    
    isSubmitting.value = true
    error.value = null
    
    try {
      // Submit as trial analysis (no auth required)
      const response = await apiClient.post<AnalysisTask>('/analyses/trial', {
        url,
        analysisType: 'full_seo',
        isTrial: true
      })
      
      if (response.data) {
        const trialData: TrialAnalysis = {
          ...response.data,
          isTrial: true
        }
        
        trialAnalysis.value = trialData
        hasUsedTrial.value = true
        
        // Store in localStorage
        localStorage.setItem('trial_analysis_used', 'true')
        localStorage.setItem('trial_analysis_data', JSON.stringify(trialData))
        
        // Start polling for results
        pollTrialAnalysisStatus(trialData.id)
        
        return trialData
      }
      
      return null
    } catch (err: any) {
      console.error('Failed to submit trial analysis:', err)
      
      if (err.response?.status === 429) {
        error.value = 'Too many trial requests. Please try again later.'
      } else if (err.response?.data?.message) {
        error.value = err.response.data.message
      } else {
        error.value = 'Failed to start trial analysis. Please try again.'
      }
      
      return null
    } finally {
      isSubmitting.value = false
    }
  }
  
  const pollTrialAnalysisStatus = async (analysisId: string) => {
    const maxAttempts = 60 // 5 minutes with 5-second intervals
    let attempts = 0
    
    const poll = async () => {
      if (attempts >= maxAttempts) {
        error.value = 'Analysis timed out. Please try again.'
        return
      }
      
      try {
        const response = await apiClient.get<AnalysisTask>(`/analyses/trial/${analysisId}`)
        
        if (response.data) {
          const trialData: TrialAnalysis = {
            ...response.data,
            isTrial: true
          }
          
          trialAnalysis.value = trialData
          localStorage.setItem('trial_analysis_data', JSON.stringify(trialData))
          
          // Continue polling if still in progress
          if (response.data.status === 'PENDING' || response.data.status === 'IN_PROGRESS') {
            attempts++
            setTimeout(poll, 5000) // Poll every 5 seconds
          }
        }
      } catch (err) {
        console.error('Failed to poll trial analysis status:', err)
        attempts++
        setTimeout(poll, 5000)
      }
    }
    
    // Start polling
    poll()
  }
  
  const clearTrialAnalysis = () => {
    trialAnalysis.value = null
    error.value = null
  }
  
  const resetTrial = () => {
    // This should only be used for development/testing
    if (import.meta.env.DEV) {
      localStorage.removeItem('trial_analysis_used')
      localStorage.removeItem('trial_analysis_data')
      hasUsedTrial.value = false
      trialAnalysis.value = null
      error.value = null
    }
  }
  
  const clearError = () => {
    error.value = null
  }
  
  // Initialize on store creation
  initializeTrialState()
  
  return {
    // State
    trialAnalysis: readonly(trialAnalysis),
    isSubmitting: readonly(isSubmitting),
    error: readonly(error),
    hasUsedTrial: readonly(hasUsedTrial),
    
    // Getters
    canUseTrial,
    isTrialComplete,
    
    // Actions
    submitTrialAnalysis,
    clearTrialAnalysis,
    resetTrial,
    clearError,
  }
})