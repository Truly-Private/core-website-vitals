<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysis'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import type { AnalysisTask, AnalysisStatus } from '@/types/analysis.types'

const router = useRouter()
const analysisStore = useAnalysisStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isLoading = ref(true)
const selectedAnalyses = ref<string[]>([])
const showFilters = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = ref({
  status: '' as AnalysisStatus | '',
  dateRange: 'all' as 'all' | 'today' | 'week' | 'month' | 'custom',
  customDateStart: '',
  customDateEnd: '',
  searchQuery: ''
})

const statusOptions = [
  { value: '', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'SUCCESS', label: 'Completed' },
  { value: 'FAILED', label: 'Failed' },
  { value: 'CANCELLED', label: 'Cancelled' }
]

const dateRangeOptions = [
  { value: 'all', label: 'All Time' },
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
  { value: 'custom', label: 'Custom Range' }
]

const statusColors = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  SUCCESS: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  CANCELLED: 'bg-gray-100 text-gray-800'
}

const filteredAnalyses = computed(() => {
  let analyses = analysisStore.analyses
  
  // Apply status filter
  if (filters.value.status) {
    analyses = analyses.filter(a => a.status === filters.value.status)
  }
  
  // Apply search filter
  if (filters.value.searchQuery) {
    const query = filters.value.searchQuery.toLowerCase()
    analyses = analyses.filter(a => 
      a.url_analyzed.toLowerCase().includes(query) ||
      a.analysis_type.toLowerCase().includes(query)
    )
  }
  
  // Apply date range filter
  if (filters.value.dateRange !== 'all') {
    const now = new Date()
    const startDate = new Date()
    
    switch (filters.value.dateRange) {
      case 'today':
        startDate.setHours(0, 0, 0, 0)
        break
      case 'week':
        startDate.setDate(now.getDate() - 7)
        break
      case 'month':
        startDate.setMonth(now.getMonth() - 1)
        break
      case 'custom':
        if (filters.value.customDateStart) {
          startDate.setTime(new Date(filters.value.customDateStart).getTime())
        }
        break
    }
    
    analyses = analyses.filter(a => {
      const analysisDate = new Date(a.submitted_at)
      let inRange = analysisDate >= startDate
      
      if (filters.value.dateRange === 'custom' && filters.value.customDateEnd) {
        const endDate = new Date(filters.value.customDateEnd)
        endDate.setHours(23, 59, 59, 999)
        inRange = inRange && analysisDate <= endDate
      }
      
      return inRange
    })
  }
  
  return analyses
})

const paginatedAnalyses = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAnalyses.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredAnalyses.value.length / pageSize.value)
})

const allSelected = computed(() => {
  return paginatedAnalyses.value.length > 0 && 
         paginatedAnalyses.value.every(a => selectedAnalyses.value.includes(a.id))
})

const someSelected = computed(() => {
  return selectedAnalyses.value.length > 0 && !allSelected.value
})

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  try {
    await analysisStore.fetchAnalyses()
  } catch (error) {
    console.error('Failed to load analyses:', error)
    uiStore.showNotification('Failed to load analysis history', 'error')
  } finally {
    isLoading.value = false
  }
})

const viewAnalysis = (analysisId: string) => {
  router.push({ name: 'analysis-result', params: { id: analysisId } })
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    selectedAnalyses.value = []
  } else {
    selectedAnalyses.value = paginatedAnalyses.value.map(a => a.id)
  }
}

const toggleSelect = (analysisId: string) => {
  const index = selectedAnalyses.value.indexOf(analysisId)
  if (index > -1) {
    selectedAnalyses.value.splice(index, 1)
  } else {
    selectedAnalyses.value.push(analysisId)
  }
}

const deleteSelectedAnalyses = async () => {
  if (selectedAnalyses.value.length === 0) return
  
  const confirmed = await uiStore.showConfirmDialog(
    'Delete Analyses',
    `Are you sure you want to delete ${selectedAnalyses.value.length} selected analyses? This action cannot be undone.`,
    'Delete',
    'danger'
  )
  
  if (confirmed) {
    try {
      await analysisStore.deleteAnalyses(selectedAnalyses.value)
      selectedAnalyses.value = []
      uiStore.showNotification('Analyses deleted successfully', 'success')
    } catch (error) {
      console.error('Failed to delete analyses:', error)
      uiStore.showNotification('Failed to delete analyses', 'error')
    }
  }
}

const retryAnalysis = async (analysisId: string) => {
  try {
    await analysisStore.retryAnalysis(analysisId)
    uiStore.showNotification('Analysis restarted', 'success')
  } catch (error) {
    console.error('Failed to retry analysis:', error)
    uiStore.showNotification('Failed to retry analysis', 'error')
  }
}

const cancelAnalysis = async (analysisId: string) => {
  const confirmed = await uiStore.showConfirmDialog(
    'Cancel Analysis',
    'Are you sure you want to cancel this analysis?',
    'Cancel Analysis',
    'danger'
  )
  
  if (confirmed) {
    try {
      await analysisStore.cancelAnalysis(analysisId)
      uiStore.showNotification('Analysis cancelled', 'success')
    } catch (error) {
      console.error('Failed to cancel analysis:', error)
      uiStore.showNotification('Failed to cancel analysis', 'error')
    }
  }
}

const exportAnalysis = async (analysisId: string, format: string) => {
  try {
    const blob = await analysisStore.exportAnalysis(analysisId, format)
    
    // Create download link
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analysis-${analysisId}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    uiStore.showNotification('Export started', 'success')
  } catch (error) {
    console.error('Export failed:', error)
    uiStore.showNotification('Export failed', 'error')
  }
}

const clearFilters = () => {
  filters.value = {
    status: '',
    dateRange: 'all',
    customDateStart: '',
    customDateEnd: '',
    searchQuery: ''
  }
  currentPage.value = 1
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

const getAnalysisTypeIcon = (type: string) => {
  switch (type) {
    case 'full_seo': return 'search'
    case 'technical_seo': return 'settings'
    case 'content_analysis': return 'file-text'
    case 'performance_audit': return 'zap'
    default: return 'globe'
  }
}

const canRetry = (analysis: AnalysisTask) => {
  return analysis.status === 'FAILED'
}

const canCancel = (analysis: AnalysisTask) => {
  return analysis.status === 'PENDING' || analysis.status === 'IN_PROGRESS'
}

const canExport = (analysis: AnalysisTask) => {
  return analysis.status === 'SUCCESS'
}

const startNewAnalysis = () => {
  router.push({ name: 'analysis' })
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
              {{ $t('analysis.history.title') }}
            </h1>
            <p class="text-gray-600">
              View and manage your SEO analysis history
            </p>
          </div>
          
          <div class="flex items-center space-x-4">
            <button
              @click="showFilters = !showFilters"
              class="btn btn-outline"
              :class="{ 'btn-primary': showFilters }"
            >
              <i class="lucide-filter w-4 h-4 mr-2"></i>
              {{ $t('common.filter') }}
            </button>
            
            <button
              @click="startNewAnalysis"
              class="btn btn-primary"
            >
              <i class="lucide-plus w-4 h-4 mr-2"></i>
              {{ $t('analysis.new_analysis') }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Filters Panel -->
    <div v-if="showFilters" class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- Search -->
          <div>
            <label for="search" class="block text-sm font-medium text-gray-700 mb-1">
              {{ $t('common.search') }}
            </label>
            <input
              id="search"
              v-model="filters.searchQuery"
              type="text"
              placeholder="Search URLs or analysis types..."
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          
          <!-- Status Filter -->
          <div>
            <label for="status" class="block text-sm font-medium text-gray-700 mb-1">
              {{ $t('analysis.history.filters.status') }}
            </label>
            <select
              id="status"
              v-model="filters.status"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <!-- Date Range -->
          <div>
            <label for="dateRange" class="block text-sm font-medium text-gray-700 mb-1">
              {{ $t('analysis.history.filters.date_range') }}
            </label>
            <select
              id="dateRange"
              v-model="filters.dateRange"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option v-for="option in dateRangeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          
          <!-- Actions -->
          <div class="flex items-end space-x-2">
            <button
              @click="clearFilters"
              class="btn btn-outline"
            >
              Clear Filters
            </button>
          </div>
        </div>
        
        <!-- Custom Date Range -->
        <div v-if="filters.dateRange === 'custom'" class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label for="customDateStart" class="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="customDateStart"
              v-model="filters.customDateStart"
              type="date"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
          <div>
            <label for="customDateEnd" class="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="customDateEnd"
              v-model="filters.customDateEnd"
              type="date"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Bulk Actions -->
      <div v-if="selectedAnalyses.length > 0" class="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <i class="lucide-check-circle w-5 h-5 text-blue-600 mr-2"></i>
            <span class="text-sm font-medium text-blue-900">
              {{ selectedAnalyses.length }} analyses selected
            </span>
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="deleteSelectedAnalyses"
              class="btn btn-danger btn-sm"
            >
              <i class="lucide-trash-2 w-4 h-4 mr-1"></i>
              Delete Selected
            </button>
            <button
              @click="selectedAnalyses = []"
              class="btn btn-outline btn-sm"
            >
              Clear Selection
            </button>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="flex items-center justify-center py-12">
        <div class="text-center">
          <i class="lucide-loader-2 w-8 h-8 animate-spin text-primary-600 mx-auto mb-4"></i>
          <p class="text-gray-600">Loading analysis history...</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredAnalyses.length === 0" class="text-center py-12">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 mb-4">
          <i class="lucide-search w-6 h-6 text-gray-400"></i>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{ filters.searchQuery || filters.status || filters.dateRange !== 'all' 
            ? 'No analyses found' 
            : 'No analyses yet' 
          }}
        </h3>
        <p class="text-gray-600 mb-4">
          {{ filters.searchQuery || filters.status || filters.dateRange !== 'all'
            ? 'Try adjusting your filters or search terms.'
            : 'Get started by running your first SEO analysis.'
          }}
        </p>
        <button
          v-if="!filters.searchQuery && !filters.status && filters.dateRange === 'all'"
          @click="startNewAnalysis"
          class="btn btn-primary"
        >
          <i class="lucide-plus w-4 h-4 mr-2"></i>
          {{ $t('analysis.new_analysis') }}
        </button>
        <button
          v-else
          @click="clearFilters"
          class="btn btn-outline"
        >
          Clear Filters
        </button>
      </div>

      <!-- Analysis Table -->
      <div v-else class="bg-white shadow rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate="someSelected"
                    @change="toggleSelectAll"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  URL
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr
                v-for="analysis in paginatedAnalyses"
                :key="analysis.id"
                class="hover:bg-gray-50"
              >
                <td class="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    :checked="selectedAnalyses.includes(analysis.id)"
                    @change="toggleSelect(analysis.id)"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <i :class="`lucide-${getAnalysisTypeIcon(analysis.analysis_type)} w-4 h-4 text-gray-400 mr-2`"></i>
                    <div>
                      <div class="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {{ analysis.url_analyzed }}
                      </div>
                      <div class="text-sm text-gray-500">
                        {{ analysis.analysis_type.replace('_', ' ').toUpperCase() }}
                      </div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="text-sm text-gray-900 capitalize">
                    {{ analysis.analysis_type.replace('_', ' ') }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                    :class="statusColors[analysis.status]"
                  >
                    <i :class="`lucide-${getStatusIcon(analysis.status)} w-3 h-3 mr-1`"></i>
                    {{ $t(`analysis.status.${analysis.status}`) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <span v-if="analysis.results?.overall_score">
                    {{ analysis.results.overall_score }}%
                  </span>
                  <span v-else class="text-gray-400">-</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDate(analysis.submitted_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div class="flex items-center space-x-2">
                    <button
                      @click="viewAnalysis(analysis.id)"
                      class="text-primary-600 hover:text-primary-900"
                    >
                      <i class="lucide-eye w-4 h-4"></i>
                    </button>
                    
                    <button
                      v-if="canRetry(analysis)"
                      @click="retryAnalysis(analysis.id)"
                      class="text-blue-600 hover:text-blue-900"
                      title="Retry analysis"
                    >
                      <i class="lucide-refresh-cw w-4 h-4"></i>
                    </button>
                    
                    <button
                      v-if="canCancel(analysis)"
                      @click="cancelAnalysis(analysis.id)"
                      class="text-red-600 hover:text-red-900"
                      title="Cancel analysis"
                    >
                      <i class="lucide-x w-4 h-4"></i>
                    </button>
                    
                    <div v-if="canExport(analysis)" class="relative inline-block text-left">
                      <button
                        class="text-gray-600 hover:text-gray-900 dropdown-toggle"
                        title="Export analysis"
                      >
                        <i class="lucide-download w-4 h-4"></i>
                      </button>
                      <div class="dropdown-menu">
                        <button
                          @click="exportAnalysis(analysis.id, 'pdf')"
                          class="dropdown-item"
                        >
                          <i class="lucide-file-pdf w-4 h-4 mr-2"></i>
                          PDF
                        </button>
                        <button
                          @click="exportAnalysis(analysis.id, 'csv')"
                          class="dropdown-item"
                        >
                          <i class="lucide-file-spreadsheet w-4 h-4 mr-2"></i>
                          CSV
                        </button>
                        <button
                          @click="exportAnalysis(analysis.id, 'json')"
                          class="dropdown-item"
                        >
                          <i class="lucide-file-code w-4 h-4 mr-2"></i>
                          JSON
                        </button>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
          <div class="flex items-center justify-between">
            <div class="flex-1 flex justify-between sm:hidden">
              <button
                @click="currentPage = Math.max(1, currentPage - 1)"
                :disabled="currentPage === 1"
                class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                @click="currentPage = Math.min(totalPages, currentPage + 1)"
                :disabled="currentPage === totalPages"
                class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
            <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p class="text-sm text-gray-700">
                  Showing
                  <span class="font-medium">{{ (currentPage - 1) * pageSize + 1 }}</span>
                  to
                  <span class="font-medium">{{ Math.min(currentPage * pageSize, filteredAnalyses.length) }}</span>
                  of
                  <span class="font-medium">{{ filteredAnalyses.length }}</span>
                  results
                </p>
              </div>
              <div>
                <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    @click="currentPage = Math.max(1, currentPage - 1)"
                    :disabled="currentPage === 1"
                    class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    <i class="lucide-chevron-left w-4 h-4"></i>
                  </button>
                  
                  <button
                    v-for="page in Array.from({ length: totalPages }, (_, i) => i + 1)"
                    :key="page"
                    @click="currentPage = page"
                    :class="[
                      page === currentPage
                        ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50',
                      'relative inline-flex items-center px-4 py-2 border text-sm font-medium'
                    ]"
                  >
                    {{ page }}
                  </button>
                  
                  <button
                    @click="currentPage = Math.min(totalPages, currentPage + 1)"
                    :disabled="currentPage === totalPages"
                    class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    <i class="lucide-chevron-right w-4 h-4"></i>
                  </button>
                </nav>
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

/* Dropdown styling */
.dropdown-toggle:focus + .dropdown-menu,
.dropdown-toggle:hover + .dropdown-menu {
  display: block;
}

.dropdown-menu {
  @apply absolute right-0 mt-2 w-32 bg-white rounded-md shadow-lg z-50 border border-gray-200;
  display: none;
}

.dropdown-item {
  @apply flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left;
}

/* Focus states */
input:focus, select:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Checkbox indeterminate state */
input[type="checkbox"]:indeterminate {
  background-color: #3b82f6;
  border-color: #3b82f6;
}

/* Transition effects */
button, input, select {
  transition: all 0.2s ease-in-out;
}

/* Table hover effects */
tbody tr:hover {
  background-color: #f9fafb;
}

/* Pagination styling */
.pagination-button {
  @apply relative inline-flex items-center px-4 py-2 border text-sm font-medium;
}

.pagination-button:hover {
  @apply bg-gray-50;
}

.pagination-button:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.pagination-button.active {
  @apply z-10 bg-primary-50 border-primary-500 text-primary-600;
}
</style>