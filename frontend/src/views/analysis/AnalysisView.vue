<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAnalysisStore } from '@/stores/analysis'
import { useUIStore } from '@/stores/ui'
import type { AnalysisType } from '@/types/analysis.types'

const router = useRouter()
const authStore = useAuthStore()
const analysisStore = useAnalysisStore()
const uiStore = useUIStore()

const isSubmitting = ref(false)
const showAdvancedOptions = ref(false)
const isBatchMode = ref(false)

const form = reactive({
  url: '',
  analysisType: 'full_seo' as AnalysisType,
  targetKeywords: '',
  customOptions: {
    includeImages: true,
    includeLinks: true,
    includeMetadata: true,
    includePerformance: true,
    includeTechnicalSeo: true,
    includeContent: true,
    includeAccessibility: true,
    includeSchema: true,
    followRedirects: true,
    userAgent: 'CoreWebsiteVitals Bot',
    timeout: 30,
    maxDepth: 1,
    includeSubdomains: false,
    excludePatterns: []
  }
})

const batchForm = reactive({
  urls: '',
  analysisType: 'full_seo' as AnalysisType,
  targetKeywords: '',
  customOptions: {
    includeImages: true,
    includeLinks: true,
    includeMetadata: true,
    includePerformance: true,
    includeTechnicalSeo: true,
    includeContent: true,
    includeAccessibility: true,
    includeSchema: true,
    followRedirects: true,
    userAgent: 'CoreWebsiteVitals Bot',
    timeout: 30,
    maxDepth: 1,
    includeSubdomains: false,
    excludePatterns: []
  }
})

// Computed properties for form binding
const currentAnalysisType = computed({
  get: () => isBatchMode.value ? batchForm.analysisType : form.analysisType,
  set: (value) => {
    if (isBatchMode.value) {
      batchForm.analysisType = value
    } else {
      form.analysisType = value
    }
  }
})

const currentTargetKeywords = computed({
  get: () => isBatchMode.value ? batchForm.targetKeywords : form.targetKeywords,
  set: (value) => {
    if (isBatchMode.value) {
      batchForm.targetKeywords = value
    } else {
      form.targetKeywords = value
    }
  }
})

const errors = reactive({
  url: '',
  urls: '',
  analysisType: '',
  general: ''
})

const analysisTypes = [
  {
    value: 'full_seo',
    label: 'Full SEO Analysis',
    description: 'Complete SEO audit including technical, content, and performance analysis',
    icon: 'search'
  },
  {
    value: 'technical_seo',
    label: 'Technical SEO',
    description: 'Focus on technical aspects like site structure, crawlability, and indexing',
    icon: 'settings'
  },
  {
    value: 'content_analysis',
    label: 'Content Analysis',
    description: 'Analyze content quality, keyword optimization, and readability',
    icon: 'file-text'
  },
  {
    value: 'performance_audit',
    label: 'Performance Audit',
    description: 'Core Web Vitals, loading speed, and performance optimization',
    icon: 'zap'
  }
]

const userAgents = [
  'CoreWebsiteVitals Bot',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]

onMounted(() => {
  // Redirect to login if not authenticated
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  // Check URL parameter for prefilled URL
  const urlParam = router.currentRoute.value.query.url as string
  if (urlParam) {
    form.url = urlParam
  }
})

const validateForm = () => {
  // Reset errors
  Object.keys(errors).forEach(key => {
    errors[key as keyof typeof errors] = ''
  })
  
  let isValid = true
  
  if (isBatchMode.value) {
    // Batch mode validation
    if (!batchForm.urls.trim()) {
      errors.urls = 'URLs are required'
      isValid = false
    } else {
      const urls = batchForm.urls.split('\n').filter(url => url.trim())
      if (urls.length === 0) {
        errors.urls = 'At least one URL is required'
        isValid = false
      } else if (urls.length > 10) {
        errors.urls = 'Maximum 10 URLs allowed per batch'
        isValid = false
      } else {
        // Validate each URL
        const invalidUrls = urls.filter(url => !isValidUrl(url.trim()))
        if (invalidUrls.length > 0) {
          errors.urls = `Invalid URLs: ${invalidUrls.join(', ')}`
          isValid = false
        }
      }
    }
  } else {
    // Single URL validation
    if (!form.url.trim()) {
      errors.url = 'URL is required'
      isValid = false
    } else if (!isValidUrl(form.url.trim())) {
      errors.url = 'Please enter a valid URL'
      isValid = false
    }
  }
  
  return isValid
}

const isValidUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`)
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  isSubmitting.value = true
  
  try {
    if (isBatchMode.value) {
      // Handle batch analysis
      const urls = batchForm.urls.split('\n')
        .filter(url => url.trim())
        .map(url => url.trim())
      
      const results = await analysisStore.submitBatchAnalysis({
        urls,
        analysisType: batchForm.analysisType,
        targetKeywords: batchForm.targetKeywords.split(',').map(k => k.trim()).filter(k => k),
        customOptions: batchForm.customOptions
      })
      
      uiStore.showNotification(
        `Batch analysis started for ${urls.length} URLs. You'll be notified when complete.`,
        'success'
      )
      
      // Redirect to history page
      router.push({ name: 'analysis-history' })
    } else {
      // Handle single URL analysis
      const result = await analysisStore.submitAnalysis({
        url: form.url,
        analysisType: form.analysisType,
        targetKeywords: form.targetKeywords.split(',').map(k => k.trim()).filter(k => k),
        customOptions: form.customOptions
      })
      
      uiStore.showNotification(
        'Analysis started! You can track progress in your dashboard.',
        'success'
      )
      
      // Redirect to analysis result page
      router.push({ 
        name: 'analysis-result', 
        params: { id: result.id } 
      })
    }
  } catch (error: any) {
    console.error('Analysis submission error:', error)
    
    if (error.message?.includes('subscription')) {
      errors.general = 'Your subscription limit has been reached. Please upgrade to continue.'
    } else if (error.message?.includes('rate limit')) {
      errors.general = 'Too many requests. Please try again later.'
    } else {
      errors.general = 'Failed to start analysis. Please try again.'
    }
  } finally {
    isSubmitting.value = false
  }
}

const toggleBatchMode = () => {
  isBatchMode.value = !isBatchMode.value
  // Reset forms when switching modes
  form.url = ''
  batchForm.urls = ''
  Object.keys(errors).forEach(key => {
    errors[key as keyof typeof errors] = ''
  })
}

const addExcludePattern = () => {
  const pattern = prompt('Enter URL pattern to exclude (e.g., /admin/, *.pdf):')
  if (pattern && pattern.trim()) {
    const currentForm = isBatchMode.value ? batchForm : form
    currentForm.customOptions.excludePatterns.push(pattern.trim())
  }
}

const removeExcludePattern = (index: number) => {
  const currentForm = isBatchMode.value ? batchForm : form
  currentForm.customOptions.excludePatterns.splice(index, 1)
}

const loadSampleUrl = () => {
  form.url = 'https://example.com'
}

const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText()
    if (isBatchMode.value) {
      batchForm.urls = text
    } else {
      form.url = text
    }
    uiStore.showNotification('Pasted from clipboard', 'success')
  } catch (error) {
    uiStore.showNotification('Failed to paste from clipboard', 'error')
  }
}

const getAnalysisTypeIcon = (type: AnalysisType) => {
  const typeConfig = analysisTypes.find(t => t.value === type)
  return typeConfig?.icon || 'search'
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
              {{ isBatchMode ? $t('analysis.batch.title') : $t('analysis.new_analysis') }}
            </h1>
            <p class="text-gray-600">
              {{ isBatchMode ? $t('analysis.batch.description') : 'Analyze your website\'s SEO performance' }}
            </p>
          </div>
          
          <div class="flex items-center space-x-4">
            <button
              @click="toggleBatchMode"
              class="btn btn-outline"
            >
              <i :class="isBatchMode ? 'lucide-link' : 'lucide-layers'" class="w-4 h-4 mr-2"></i>
              {{ isBatchMode ? 'Single URL' : 'Batch Mode' }}
            </button>
            
            <router-link
              :to="{ name: 'analysis-history' }"
              class="btn btn-outline"
            >
              <i class="lucide-history w-4 h-4 mr-2"></i>
              {{ $t('navigation.history') }}
            </router-link>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <form @submit.prevent="handleSubmit" class="space-y-8">
        <!-- URL Input Section -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">
            {{ isBatchMode ? $t('analysis.batch.urls') : $t('analysis.url') }}
          </h2>
          
          <div v-if="!isBatchMode" class="space-y-4">
            <div>
              <label for="url" class="block text-sm font-medium text-gray-700 mb-2">
                {{ $t('analysis.url') }}
              </label>
              <div class="flex">
                <input
                  id="url"
                  v-model="form.url"
                  type="url"
                  required
                  class="flex-1 min-w-0 block w-full px-3 py-2 border border-gray-300 rounded-l-md focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  :class="{ 'border-red-300': errors.url }"
                  :placeholder="$t('analysis.url_placeholder')"
                />
                <button
                  type="button"
                  @click="pasteFromClipboard"
                  class="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 hover:bg-gray-100 text-sm"
                >
                  <i class="lucide-clipboard w-4 h-4"></i>
                </button>
              </div>
              <div v-if="errors.url" class="mt-1 text-sm text-red-600">
                {{ errors.url }}
              </div>
              <div class="mt-2 flex items-center space-x-2">
                <button
                  type="button"
                  @click="loadSampleUrl"
                  class="text-sm text-primary-600 hover:text-primary-500"
                >
                  Use sample URL
                </button>
              </div>
            </div>
          </div>
          
          <div v-else class="space-y-4">
            <div>
              <label for="urls" class="block text-sm font-medium text-gray-700 mb-2">
                {{ $t('analysis.batch.urls') }}
              </label>
              <textarea
                id="urls"
                v-model="batchForm.urls"
                rows="6"
                required
                class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                :class="{ 'border-red-300': errors.urls }"
                :placeholder="$t('analysis.batch.urls_placeholder')"
              ></textarea>
              <div v-if="errors.urls" class="mt-1 text-sm text-red-600">
                {{ errors.urls }}
              </div>
              <div class="mt-2 flex items-center justify-between">
                <p class="text-sm text-gray-500">
                  {{ $t('analysis.batch.max_urls', { count: 10 }) }}
                </p>
                <button
                  type="button"
                  @click="pasteFromClipboard"
                  class="text-sm text-primary-600 hover:text-primary-500"
                >
                  <i class="lucide-clipboard w-4 h-4 mr-1"></i>
                  Paste from clipboard
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Analysis Type Selection -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">
            {{ $t('analysis.analysis_type') }}
          </h2>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="type in analysisTypes"
              :key="type.value"
              class="relative"
            >
              <input
                :id="`type-${type.value}`"
                v-model="currentAnalysisType"
                :value="type.value"
                type="radio"
                name="analysisType"
                class="sr-only"
              />
              <label
                :for="`type-${type.value}`"
                class="block cursor-pointer rounded-lg border-2 p-4 transition-colors"
                :class="currentAnalysisType === type.value 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <div class="flex items-start">
                  <div class="flex-shrink-0">
                    <i :class="`lucide-${type.icon} w-6 h-6 text-primary-600`"></i>
                  </div>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-gray-900">
                      {{ type.label }}
                    </h3>
                    <p class="text-sm text-gray-500">
                      {{ type.description }}
                    </p>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Target Keywords -->
        <div class="bg-white shadow rounded-lg p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-4">
            {{ $t('analysis.target_keywords') }}
          </h2>
          
          <div>
            <label for="keywords" class="block text-sm font-medium text-gray-700 mb-2">
              {{ $t('analysis.target_keywords') }}
            </label>
            <input
              id="keywords"
              v-model="currentTargetKeywords"
              type="text"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              :placeholder="$t('analysis.keywords_placeholder')"
            />
            <p class="mt-2 text-sm text-gray-500">
              Optional: Enter comma-separated keywords to optimize for
            </p>
          </div>
        </div>

        <!-- Advanced Options -->
        <div class="bg-white shadow rounded-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-medium text-gray-900">
              {{ $t('analysis.advanced_options') }}
            </h2>
            <button
              type="button"
              @click="showAdvancedOptions = !showAdvancedOptions"
              class="text-primary-600 hover:text-primary-500"
            >
              <i :class="showAdvancedOptions ? 'lucide-chevron-up' : 'lucide-chevron-down'" class="w-5 h-5"></i>
            </button>
          </div>
          
          <div v-if="showAdvancedOptions" class="space-y-6">
            <!-- Analysis Options -->
            <div>
              <h3 class="text-sm font-medium text-gray-900 mb-3">Analysis Options</h3>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeImages"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Images</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeLinks"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Links</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeMetadata"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Metadata</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includePerformance"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Performance</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeTechnicalSeo"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Technical SEO</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeContent"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Content</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeAccessibility"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Accessibility</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeSchema"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span class="ml-2 text-sm text-gray-900">Schema</span>
                </label>
              </div>
            </div>

            <!-- Crawl Settings -->
            <div>
              <h3 class="text-sm font-medium text-gray-900 mb-3">Crawl Settings</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label for="userAgent" class="block text-sm font-medium text-gray-700 mb-1">
                    User Agent
                  </label>
                  <select
                    id="userAgent"
                    v-model="(isBatchMode ? batchForm : form).customOptions.userAgent"
                    class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option v-for="agent in userAgents" :key="agent" :value="agent">
                      {{ agent }}
                    </option>
                  </select>
                </div>
                <div>
                  <label for="timeout" class="block text-sm font-medium text-gray-700 mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    id="timeout"
                    v-model.number="(isBatchMode ? batchForm : form).customOptions.timeout"
                    type="number"
                    min="10"
                    max="120"
                    class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label for="maxDepth" class="block text-sm font-medium text-gray-700 mb-1">
                    Max Depth
                  </label>
                  <input
                    id="maxDepth"
                    v-model.number="(isBatchMode ? batchForm : form).customOptions.maxDepth"
                    type="number"
                    min="1"
                    max="5"
                    class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                <div class="flex items-center">
                  <input
                    id="followRedirects"
                    v-model="(isBatchMode ? batchForm : form).customOptions.followRedirects"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <label for="followRedirects" class="ml-2 text-sm text-gray-900">
                    Follow Redirects
                  </label>
                </div>
                <div class="flex items-center">
                  <input
                    id="includeSubdomains"
                    v-model="(isBatchMode ? batchForm : form).customOptions.includeSubdomains"
                    type="checkbox"
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <label for="includeSubdomains" class="ml-2 text-sm text-gray-900">
                    Include Subdomains
                  </label>
                </div>
              </div>
            </div>

            <!-- Exclude Patterns -->
            <div>
              <h3 class="text-sm font-medium text-gray-900 mb-3">Exclude Patterns</h3>
              <div class="space-y-2">
                <div
                  v-for="(pattern, index) in (isBatchMode ? batchForm : form).customOptions.excludePatterns"
                  :key="index"
                  class="flex items-center space-x-2"
                >
                  <code class="flex-1 px-2 py-1 text-sm bg-gray-100 rounded">{{ pattern }}</code>
                  <button
                    type="button"
                    @click="removeExcludePattern(index)"
                    class="text-red-600 hover:text-red-500"
                  >
                    <i class="lucide-x w-4 h-4"></i>
                  </button>
                </div>
                <button
                  type="button"
                  @click="addExcludePattern"
                  class="text-primary-600 hover:text-primary-500 text-sm"
                >
                  <i class="lucide-plus w-4 h-4 mr-1"></i>
                  Add exclude pattern
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errors.general" class="bg-red-50 border border-red-200 rounded-md p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <i class="lucide-alert-circle w-5 h-5 text-red-400"></i>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                Analysis Error
              </h3>
              <div class="mt-2 text-sm text-red-700">
                {{ errors.general }}
              </div>
            </div>
          </div>
        </div>

        <!-- Submit Button -->
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-500">
            <i class="lucide-info w-4 h-4 mr-1"></i>
            Analysis typically takes 1-3 minutes to complete
          </div>
          
          <button
            type="submit"
            :disabled="isSubmitting"
            class="btn btn-primary btn-lg"
          >
            <i v-if="isSubmitting" class="lucide-loader-2 w-5 h-5 mr-2 animate-spin"></i>
            <i v-else :class="`lucide-${getAnalysisTypeIcon((isBatchMode ? batchForm : form).analysisType)} w-5 h-5 mr-2`"></i>
            {{ isSubmitting ? $t('common.loading') : $t('analysis.submit_analysis') }}
          </button>
        </div>
      </form>
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

/* Focus states */
input:focus, select:focus, textarea:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Transition effects */
button, input, select, textarea {
  transition: all 0.2s ease-in-out;
}

/* Radio button styling */
input[type="radio"]:checked + label {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

/* Checkbox styling */
input[type="checkbox"]:checked {
  background-color: #3b82f6;
  border-color: #3b82f6;
}
</style>