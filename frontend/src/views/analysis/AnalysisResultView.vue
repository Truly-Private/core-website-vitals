<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysis'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import type { AnalysisTask, AnalysisResult } from '@/types/analysis.types'

interface Props {
  id: string
}

const props = defineProps<Props>()
const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

const analysis = ref<AnalysisTask | null>(null)
const isLoading = ref(true)
const refreshInterval = ref<number | null>(null)
const activeTab = ref('overview')
const isExporting = ref(false)
const showRawData = ref(false)

const tabs = [
  { id: 'overview', name: 'Overview', icon: 'layout-dashboard' },
  { id: 'performance', name: 'Performance', icon: 'zap' },
  { id: 'seo', name: 'SEO', icon: 'search' },
  { id: 'technical', name: 'Technical', icon: 'settings' },
  { id: 'content', name: 'Content', icon: 'file-text' },
  { id: 'accessibility', name: 'Accessibility', icon: 'eye' },
  { id: 'recommendations', name: 'Recommendations', icon: 'lightbulb' }
]

const exportFormats = [
  { value: 'pdf', label: 'PDF Report', icon: 'file-pdf' },
  { value: 'csv', label: 'CSV Data', icon: 'file-spreadsheet' },
  { value: 'json', label: 'JSON Data', icon: 'file-code' },
  { value: 'html', label: 'HTML Report', icon: 'file-html' }
]

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  SUCCESS: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-gray-100 text-gray-800'
}

const scoreColors = computed(() => {
  if (!analysis.value?.results?.overall_score) return 'text-gray-500'
  
  const score = analysis.value.results.overall_score
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  if (score >= 50) return 'text-orange-600'
  return 'text-red-600'
})

const scoreRing = computed(() => {
  if (!analysis.value?.results?.overall_score) return 'stroke-gray-300'
  
  const score = analysis.value.results.overall_score
  if (score >= 90) return 'stroke-green-500'
  if (score >= 70) return 'stroke-yellow-500'
  if (score >= 50) return 'stroke-orange-500'
  return 'stroke-red-500'
})

const isCompleted = computed(() => {
  return analysis.value?.status === 'SUCCESS' || analysis.value?.status === 'FAILED'
})

const canRetry = computed(() => {
  return analysis.value?.status === 'FAILED'
})

const canCancel = computed(() => {
  return analysis.value?.status === 'PENDING' || analysis.value?.status === 'IN_PROGRESS'
})

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  await loadAnalysis()
  
  // Set up polling for non-completed analyses
  if (!isCompleted.value) {
    refreshInterval.value = setInterval(loadAnalysis, 5000)
  }
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

const loadAnalysis = async () => {
  try {
    const result = await analysisStore.getAnalysis(props.id)
    analysis.value = result
    
    // Stop polling if analysis is completed
    if (isCompleted.value && refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  } catch (error: any) {
    console.error('Failed to load analysis:', error)
    
    if (error.response?.status === 404) {
      uiStore.showNotification('Analysis not found', 'error')
      router.push({ name: 'analysis-history' })
    } else {
      uiStore.showNotification('Failed to load analysis', 'error')
    }
  } finally {
    isLoading.value = false
  }
}

const handleRetry = async () => {
  if (!analysis.value) return
  
  try {
    await analysisStore.retryAnalysis(analysis.value.id)
    analysis.value.status = 'PENDING'
    
    // Restart polling
    if (!refreshInterval.value) {
      refreshInterval.value = setInterval(loadAnalysis, 5000)
    }
    
    uiStore.showNotification('Analysis restarted', 'success')
  } catch (error) {
    console.error('Failed to retry analysis:', error)
    uiStore.showNotification('Failed to retry analysis', 'error')
  }
}

const handleCancel = async () => {
  if (!analysis.value) return
  
  const confirmed = await uiStore.showConfirmDialog(
    'Cancel Analysis',
    'Are you sure you want to cancel this analysis?',
    'Cancel Analysis',
    'danger'
  )
  
  if (confirmed) {
    try {
      await analysisStore.cancelAnalysis(analysis.value.id)
      analysis.value.status = 'CANCELLED'
      
      // Stop polling
      if (refreshInterval.value) {
        clearInterval(refreshInterval.value)
        refreshInterval.value = null
      }
      
      uiStore.showNotification('Analysis cancelled', 'success')
    } catch (error) {
      console.error('Failed to cancel analysis:', error)
      uiStore.showNotification('Failed to cancel analysis', 'error')
    }
  }
}

const handleExport = async (format: string) => {
  if (!analysis.value) return
  
  isExporting.value = true
  
  try {
    const blob = await analysisStore.exportAnalysis(analysis.value.id, format)
    
    // Create download link
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis-${analysis.value.id}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    uiStore.showNotification('Export started', 'success')
  } catch (error) {
    console.error('Export failed:', error)
    uiStore.showNotification('Export failed', 'error')
  } finally {
    isExporting.value = false
  }
}

const shareAnalysis = async () => {
  if (!analysis.value) return
  
  const shareUrl = `${window.location.origin}/analysis/${analysis.value.id}`
  
  try {
    await navigator.share({
      title: `SEO Analysis - ${analysis.value.url_analyzed}`,
      text: `Check out this SEO analysis result`,
      url: shareUrl
    })
  } catch (error) {
    // Fallback to clipboard
    try {
      await navigator.clipboard.writeText(shareUrl)
      uiStore.showNotification('Share link copied to clipboard', 'success')
    } catch (clipboardError) {
      uiStore.showNotification('Failed to share analysis', 'error')
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'PENDING': return 'clock'
    case 'IN_PROGRESS': return 'loader-2'
    case 'SUCCESS': return 'check-circle'
    case 'FAILED': return 'x-circle'
    case 'CANCELLED': return 'ban'
    default: return 'help-circle'
  }
}

const getRecommendationIcon = (type: string) => {
  switch (type) {
    case 'critical': return 'alert-triangle'
    case 'warning': return 'alert-circle'
    case 'info': return 'info'
    case 'success': return 'check-circle'
    default: return 'lightbulb'
  }
}

const getRecommendationColor = (type: string) => {
  switch (type) {
    case 'critical': return 'text-red-600'
    case 'warning': return 'text-yellow-600'
    case 'info': return 'text-blue-600'
    case 'success': return 'text-green-600'
    default: return 'text-gray-600'
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div class="flex items-center space-x-4">
            <router-link
              :to="{ name: 'analysis-history' }"
              class="text-gray-400 hover:text-gray-600"
            >
              <i class="lucide-arrow-left w-5 h-5"></i>
            </router-link>
            
            <div>
              <h1 class="text-2xl font-bold text-gray-900">
                Analysis Results
              </h1>
              <p v-if="analysis" class="text-gray-600 truncate max-w-md">
                {{ analysis.url_analyzed }}
              </p>
            </div>
          </div>
          
          <div class="flex items-center space-x-4">
            <div v-if="analysis" class="flex items-center space-x-2">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="statusColors[analysis.status]"
              >
                <i :class="`lucide-${getStatusIcon(analysis.status)} w-3 h-3 mr-1`"></i>
                {{ $t(`analysis.status.${analysis.status}`) }}
              </span>
              
              <span v-if="analysis.results?.overall_score" class="text-sm text-gray-500">
                Score: <span :class="scoreColors">{{ analysis.results.overall_score }}%</span>
              </span>
            </div>
            
            <div class="relative inline-block text-left">
              <button
                class="btn btn-outline dropdown-toggle"
                :disabled="!analysis || analysis.status !== 'SUCCESS'"
              >
                <i class="lucide-download w-4 h-4 mr-2"></i>
                Export
              </button>
              <div class="dropdown-menu">
                <button
                  v-for="format in exportFormats"
                  :key="format.value"
                  @click="handleExport(format.value)"
                  class="dropdown-item"
                  :disabled="isExporting"
                >
                  <i :class="`lucide-${format.icon} w-4 h-4 mr-2`"></i>
                  {{ format.label }}
                </button>
              </div>
            </div>
            
            <button
              v-if="analysis && analysis.status === 'SUCCESS'"
              @click="shareAnalysis"
              class="btn btn-outline"
            >
              <i class="lucide-share w-4 h-4 mr-2"></i>
              Share
            </button>
            
            <button
              v-if="canRetry"
              @click="handleRetry"
              class="btn btn-primary"
            >
              <i class="lucide-refresh-cw w-4 h-4 mr-2"></i>
              Retry
            </button>
            
            <button
              v-if="canCancel"
              @click="handleCancel"
              class="btn btn-danger"
            >
              <i class="lucide-x w-4 h-4 mr-2"></i>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <i class="lucide-loader-2 w-8 h-8 animate-spin text-primary-600 mx-auto mb-4"></i>
        <p class="text-gray-600">Loading analysis...</p>
      </div>
    </div>

    <!-- Main Content -->
    <main v-else-if="analysis" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- In Progress State -->
      <div v-if="analysis.status === 'IN_PROGRESS' || analysis.status === 'PENDING'" class="text-center py-12">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
          <i class="lucide-loader-2 w-6 h-6 text-blue-600 animate-spin"></i>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ analysis.status === 'PENDING' ? 'Analysis Queued' : 'Analysis in Progress' }}
        </h3>
        <p class="text-gray-600 mb-4">
          {{ analysis.status === 'PENDING' 
            ? 'Your analysis is in the queue and will start shortly.' 
            : 'We\'re analyzing your website. This usually takes 1-3 minutes.' 
          }}
        </p>
        <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div class="bg-blue-600 h-2 rounded-full animate-pulse" style="width: 45%"></div>
        </div>
        <p class="text-sm text-gray-500">
          Started {{ formatDate(analysis.submitted_at) }}
        </p>
      </div>

      <!-- Failed State -->
      <div v-else-if="analysis.status === 'FAILED'" class="text-center py-12">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
          <i class="lucide-x-circle w-6 h-6 text-red-600"></i>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          Analysis Failed
        </h3>
        <p class="text-gray-600 mb-4">
          {{ analysis.error_message || 'An error occurred during analysis. Please try again.' }}
        </p>
        <button
          @click="handleRetry"
          class="btn btn-primary"
        >
          <i class="lucide-refresh-cw w-4 h-4 mr-2"></i>
          Retry Analysis
        </button>
      </div>

      <!-- Success State -->
      <div v-else-if="analysis.status === 'SUCCESS' && analysis.results" class="space-y-8">
        <!-- Score Overview -->
        <div class="bg-white shadow rounded-lg p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-semibold text-gray-900">Overall Score</h2>
            <div class="text-sm text-gray-500">
              Analyzed {{ formatDate(analysis.completed_at || analysis.submitted_at) }}
            </div>
          </div>
          
          <div class="flex items-center justify-center">
            <div class="relative">
              <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="currentColor"
                  stroke-width="8"
                  fill="none"
                  class="text-gray-200"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  stroke="currentColor"
                  stroke-width="8"
                  fill="none"
                  :class="scoreRing"
                  :stroke-dasharray="`${(analysis.results.overall_score / 100) * 251.2} 251.2`"
                  stroke-linecap="round"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="text-3xl font-bold" :class="scoreColors">
                    {{ analysis.results.overall_score }}
                  </div>
                  <div class="text-sm text-gray-500">Score</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="bg-white shadow rounded-lg">
          <div class="border-b border-gray-200">
            <nav class="flex space-x-8 px-6" aria-label="Tabs">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="[
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center'
                ]"
              >
                <i :class="`lucide-${tab.icon} w-4 h-4 mr-2`"></i>
                {{ tab.name }}
              </button>
            </nav>
          </div>
          
          <div class="p-6">
            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-center">
                    <i class="lucide-globe w-5 h-5 text-blue-600 mr-3"></i>
                    <div>
                      <p class="text-sm font-medium text-gray-900">Pages Analyzed</p>
                      <p class="text-2xl font-bold text-gray-900">
                        {{ analysis.results.pages_analyzed || 1 }}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-center">
                    <i class="lucide-alert-triangle w-5 h-5 text-red-600 mr-3"></i>
                    <div>
                      <p class="text-sm font-medium text-gray-900">Critical Issues</p>
                      <p class="text-2xl font-bold text-gray-900">
                        {{ analysis.results.critical_issues || 0 }}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-center">
                    <i class="lucide-alert-circle w-5 h-5 text-yellow-600 mr-3"></i>
                    <div>
                      <p class="text-sm font-medium text-gray-900">Warnings</p>
                      <p class="text-2xl font-bold text-gray-900">
                        {{ analysis.results.warnings || 0 }}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div class="bg-gray-50 rounded-lg p-4">
                  <div class="flex items-center">
                    <i class="lucide-clock w-5 h-5 text-green-600 mr-3"></i>
                    <div>
                      <p class="text-sm font-medium text-gray-900">Load Time</p>
                      <p class="text-2xl font-bold text-gray-900">
                        {{ analysis.results.load_time || 'N/A' }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="analysis.results.summary" class="prose max-w-none">
                <h3>Summary</h3>
                <p>{{ analysis.results.summary }}</p>
              </div>
            </div>

            <!-- Performance Tab -->
            <div v-if="activeTab === 'performance'" class="space-y-6">
              <div v-if="analysis.results.performance" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center">
                  <div class="text-3xl font-bold text-green-600">
                    {{ analysis.results.performance.lcp || 'N/A' }}
                  </div>
                  <div class="text-sm text-gray-500">Largest Contentful Paint</div>
                </div>
                <div class="text-center">
                  <div class="text-3xl font-bold text-yellow-600">
                    {{ analysis.results.performance.fid || 'N/A' }}
                  </div>
                  <div class="text-sm text-gray-500">First Input Delay</div>
                </div>
                <div class="text-center">
                  <div class="text-3xl font-bold text-blue-600">
                    {{ analysis.results.performance.cls || 'N/A' }}
                  </div>
                  <div class="text-sm text-gray-500">Cumulative Layout Shift</div>
                </div>
              </div>
              
              <div v-if="analysis.results.performance?.recommendations" class="space-y-4">
                <h3 class="text-lg font-medium text-gray-900">Performance Recommendations</h3>
                <div
                  v-for="(recommendation, index) in analysis.results.performance.recommendations"
                  :key="index"
                  class="border-l-4 border-blue-500 pl-4 py-2"
                >
                  <p class="font-medium">{{ recommendation.title }}</p>
                  <p class="text-sm text-gray-600">{{ recommendation.description }}</p>
                </div>
              </div>
            </div>

            <!-- SEO Tab -->
            <div v-if="activeTab === 'seo'" class="space-y-6">
              <div v-if="analysis.results.seo" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Meta Tags</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Title Tag</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.title_tag ? 'Present' : 'Missing' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Meta Description</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.meta_description ? 'Present' : 'Missing' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Open Graph</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.open_graph ? 'Present' : 'Missing' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Structure</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">H1 Tags</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.h1_count || 0 }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Internal Links</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.internal_links || 0 }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">External Links</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.seo.external_links || 0 }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Technical Tab -->
            <div v-if="activeTab === 'technical'" class="space-y-6">
              <div v-if="analysis.results.technical" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Crawling</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Robots.txt</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.robots_txt ? 'Present' : 'Missing' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Sitemap</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.sitemap ? 'Present' : 'Missing' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">SSL Certificate</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.ssl ? 'Valid' : 'Invalid' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Response</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Status Code</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.status_code || 'N/A' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Response Time</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.response_time || 'N/A' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Content Type</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.technical.content_type || 'N/A' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Content Tab -->
            <div v-if="activeTab === 'content'" class="space-y-6">
              <div v-if="analysis.results.content" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Statistics</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Word Count</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.word_count || 0 }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Reading Time</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.reading_time || 'N/A' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Images</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.images_count || 0 }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Quality</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Readability Score</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.readability_score || 'N/A' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Duplicate Content</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.duplicate_content ? 'Found' : 'None' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Thin Content</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.content.thin_content ? 'Found' : 'None' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Accessibility Tab -->
            <div v-if="activeTab === 'accessibility'" class="space-y-6">
              <div v-if="analysis.results.accessibility" class="space-y-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">WCAG Compliance</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Level A</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.wcag_a ? 'Compliant' : 'Non-compliant' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Level AA</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.wcag_aa ? 'Compliant' : 'Non-compliant' }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Level AAA</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.wcag_aaa ? 'Compliant' : 'Non-compliant' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 class="text-lg font-medium text-gray-900 mb-3">Issues</h3>
                    <div class="space-y-2">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Missing Alt Text</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.missing_alt_text || 0 }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Color Contrast</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.color_contrast_issues || 0 }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Keyboard Navigation</span>
                        <span class="text-sm font-medium">
                          {{ analysis.results.accessibility.keyboard_navigation ? 'Supported' : 'Issues' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Recommendations Tab -->
            <div v-if="activeTab === 'recommendations'" class="space-y-6">
              <div v-if="analysis.results.recommendations" class="space-y-4">
                <div
                  v-for="(recommendation, index) in analysis.results.recommendations"
                  :key="index"
                  class="border rounded-lg p-4"
                >
                  <div class="flex items-start">
                    <div class="flex-shrink-0">
                      <i
                        :class="`lucide-${getRecommendationIcon(recommendation.type)} w-5 h-5 ${getRecommendationColor(recommendation.type)}`"
                      ></i>
                    </div>
                    <div class="ml-3 flex-1">
                      <h3 class="text-sm font-medium text-gray-900">
                        {{ recommendation.title }}
                      </h3>
                      <p class="text-sm text-gray-600 mt-1">
                        {{ recommendation.description }}
                      </p>
                      <div v-if="recommendation.action" class="mt-2">
                        <button class="text-sm text-primary-600 hover:text-primary-500">
                          {{ recommendation.action }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Raw Data Toggle -->
        <div class="bg-white shadow rounded-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-medium text-gray-900">Raw Data</h2>
            <button
              @click="showRawData = !showRawData"
              class="text-primary-600 hover:text-primary-500"
            >
              {{ showRawData ? 'Hide' : 'Show' }} Raw Data
            </button>
          </div>
          
          <div v-if="showRawData" class="bg-gray-50 rounded-lg p-4 overflow-auto">
            <pre class="text-sm text-gray-800">{{ JSON.stringify(analysis.results, null, 2) }}</pre>
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

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Dropdown styling */
.dropdown-toggle:focus + .dropdown-menu,
.dropdown-toggle:hover + .dropdown-menu {
  display: block;
}

.dropdown-menu {
  @apply absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-50 border border-gray-200;
  display: none;
}

.dropdown-item {
  @apply flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left;
}

.dropdown-item:disabled {
  @apply opacity-50 cursor-not-allowed;
}

/* Tab styling */
.tab-active {
  @apply border-primary-500 text-primary-600;
}

.tab-inactive {
  @apply border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300;
}

/* Progress bar animation */
.progress-bar {
  animation: progress 2s ease-in-out;
}

@keyframes progress {
  0% {
    width: 0%;
  }
  100% {
    width: 45%;
  }
}
</style>