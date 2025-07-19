<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTrialStore } from '@/stores/trial'
import { useAuthStore } from '@/stores/auth'
import PublicHeader from '@/components/layout/PublicHeader.vue'

const router = useRouter()
const route = useRoute()
const trialStore = useTrialStore()
const authStore = useAuthStore()

const analysisId = computed(() => route.params.id as string)

// Computed properties for analysis data
const analysisData = computed(() => trialStore.trialAnalysis)
const analysisResults = computed(() => analysisData.value?.results || {})
const seoAttributes = computed(() => analysisResults.value?.seo_attributes || {})
const overallScore = computed(() => analysisResults.value?.overall_score || 0)
const categories = computed(() => analysisResults.value?.categories || {})
const coreWebVitals = computed(() => analysisResults.value?.core_web_vitals || {})
const issues = computed(() => analysisResults.value?.issues || [])
const successes = computed(() => analysisResults.value?.successes || [])
const metadata = computed(() => analysisResults.value?.metadata || {})

onMounted(() => {
  // Check if this is a valid trial analysis
  if (!trialStore.trialAnalysis || trialStore.trialAnalysis.id !== analysisId.value) {
    // Redirect to home if no valid trial
    router.push({ name: 'home' })
  }
})

// Format category name for display
const formatCategoryName = (category: string) => {
  const names: Record<string, string> = {
    on_page: 'On-Page SEO',
    technical: 'Technical SEO',
    content: 'Content Quality',
    overall: 'Overall Score'
  }
  return names[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// Format metric values based on type
const formatMetricValue = (value: number, metric: string) => {
  if (metric === 'lcp' || metric.includes('time')) {
    return `${value}s`
  } else if (metric === 'dom_size') {
    return value.toString()
  } else if (metric === 'page_size') {
    return `${value} KB`
  }
  return value.toString()
}

const getScoreColor = (score: number) => {
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const getScoreBgColor = (score: number) => {
  if (score >= 90) return 'bg-green-100'
  if (score >= 70) return 'bg-yellow-100'
  return 'bg-red-100'
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'good':
      return 'check-circle'
    case 'warning':
      return 'alert-circle'
    case 'error':
      return 'x-circle'
    default:
      return 'help-circle'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'good':
      return 'text-green-600'
    case 'warning':
      return 'text-yellow-600'
    case 'error':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

// New computed properties and methods for the redesigned metadata section
const topKeywords = computed(() => {
  const keywords = metadata.value?.topKeywords || []
  return keywords.slice(0, 8) // Show top 8 keywords
})

// Title optimization methods
const getTitleScore = () => {
  const titleLength = metadata.value?.titleLength || 0
  if (titleLength >= 50 && titleLength <= 60) return 100
  if (titleLength >= 40 && titleLength < 50) return 85
  if (titleLength > 60 && titleLength <= 70) return 85
  if (titleLength >= 30 && titleLength < 40) return 70
  if (titleLength > 70 && titleLength <= 80) return 70
  return 50
}

const getTitleOptimizationStatus = () => {
  const score = getTitleScore()
  if (score >= 90) return 'Optimal'
  if (score >= 70) return 'Good'
  return 'Needs Work'
}

const getTitleOptimizationClass = () => {
  const score = getTitleScore()
  if (score >= 90) return 'bg-green-100 text-green-800'
  if (score >= 70) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const getTitleLengthRecommendation = () => {
  const titleLength = metadata.value?.titleLength || 0
  if (titleLength < 30) return 'Too short - aim for 50-60 chars'
  if (titleLength > 70) return 'Too long - aim for 50-60 chars'
  if (titleLength >= 50 && titleLength <= 60) return 'Perfect length!'
  return 'Good length'
}

// Heading structure methods
const getHeadingCount = (level: number) => {
  const key = `h${level}Count`
  return metadata.value?.[key] || 0
}

// Readability methods
const getReadabilityScore = () => {
  const contentAnalyzer = seoAttributes.value?.ContentAnalyzer || {}
  const score = contentAnalyzer.flesch_reading_ease_score
  if (score >= 60) return 'Easy'
  if (score >= 30) return 'Moderate'
  return 'Difficult'
}

const getReadabilityColor = () => {
  const contentAnalyzer = seoAttributes.value?.ContentAnalyzer || {}
  const score = contentAnalyzer.flesch_reading_ease_score || 0
  if (score >= 60) return 'text-green-600'
  if (score >= 30) return 'text-yellow-600'
  return 'text-red-600'
}

// Keyword methods
const getKeywordSize = (count: number) => {
  const maxCount = Math.max(...(topKeywords.value.map(k => k.count) || [1]))
  const minSize = 11
  const maxSize = 16
  return Math.round(minSize + ((count / maxCount) * (maxSize - minSize)))
}

// Page Speed methods
const getTTFB = () => {
  const technicalSEO = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  return technicalSEO.siteLoadingSpeedTest?.ttfb_seconds || 0
}

const getSpeedScore = () => {
  const ttfb = getTTFB()
  if (ttfb <= 0.5) return 100
  if (ttfb <= 1) return 85
  if (ttfb <= 2) return 70
  if (ttfb <= 3) return 50
  return 30
}

const getSpeedScoreColor = () => {
  const score = getSpeedScore()
  if (score >= 85) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const getSpeedScoreTextColor = () => {
  const score = getSpeedScore()
  if (score >= 85) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const getSpeedStatus = () => {
  const score = getSpeedScore()
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Good'
  return 'Needs Improvement'
}

// Mobile optimization methods
const getMobileScore = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  let score = 0
  if (technical.mobileResponsive) score += 40
  if (technical.viewport) score += 30
  if (technical.domSize < 1500) score += 30
  return score
}

const getMobileOptimizationBg = () => {
  const score = getMobileScore()
  if (score >= 90) return 'bg-green-100'
  if (score >= 70) return 'bg-yellow-100'
  return 'bg-red-100'
}

const getMobileOptimizationColor = () => {
  const score = getMobileScore()
  if (score >= 90) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const getMobileOptimizationTextColor = () => getMobileOptimizationColor()

const getMobileStatus = () => {
  const score = getMobileScore()
  if (score >= 90) return 'Fully Optimized'
  if (score >= 70) return 'Good'
  return 'Needs Work'
}

// Security methods
const getSecurityFeatures = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  let count = 0
  if (technical.hasHttps || metadata.value?.hasHttps) count++
  if (technical.hstsHeader) count++
  if (!technical.hasMixedContent) count++
  return count
}

const getSecurityBg = () => {
  const features = getSecurityFeatures()
  if (features >= 3) return 'bg-green-100'
  if (features >= 2) return 'bg-yellow-100'
  return 'bg-red-100'
}

const getSecurityColor = () => {
  const features = getSecurityFeatures()
  if (features >= 3) return 'text-green-600'
  if (features >= 2) return 'text-yellow-600'
  return 'text-red-600'
}

const getSecurityTextColor = () => getSecurityColor()

const getSecurityStatus = () => {
  const features = getSecurityFeatures()
  if (features >= 3) return 'Excellent'
  if (features >= 2) return 'Good'
  return 'Needs Improvement'
}

// Crawlability methods
const getCrawlabilityScore = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  let score = 0
  if (metadata.value?.hasRobotsTxt) score += 25
  if (metadata.value?.hasSitemap) score += 25
  if (technical.hasCanonicalTag) score += 25
  if (!technical.hasMetaNoindex) score += 25
  return score
}

const getCrawlabilityBg = () => {
  const score = getCrawlabilityScore()
  if (score >= 100) return 'bg-green-100'
  if (score >= 75) return 'bg-yellow-100'
  return 'bg-red-100'
}

const getCrawlabilityColor = () => {
  const score = getCrawlabilityScore()
  if (score >= 100) return 'text-green-600'
  if (score >= 75) return 'text-yellow-600'
  return 'text-red-600'
}

const getCrawlabilityTextColor = () => getCrawlabilityColor()

const getCrawlabilityStatus = () => {
  const score = getCrawlabilityScore()
  if (score >= 100) return 'Perfect'
  if (score >= 75) return 'Good'
  return 'Needs Work'
}

// Link profile methods
const getInternalLinksCount = () => {
  const onPage = seoAttributes.value?.OnPageAnalyzer || {}
  return onPage.internalLinksCount || 0
}

const getExternalLinksCount = () => {
  const onPage = seoAttributes.value?.OnPageAnalyzer || {}
  return onPage.externalLinksCount || 0
}

const getBrokenLinksCount = () => {
  const onPage = seoAttributes.value?.OnPageAnalyzer || {}
  return onPage.brokenLinksCount || 0
}

// Modern SEO features methods
const hasStructuredData = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  return technical.hasJsonLd || technical.hasMicrodata || technical.hasSchema
}

const hasModernImageFormats = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  return technical.usesWebPInHtml || technical.usesAvifInHtml
}

const hasCanonicalTag = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  return technical.hasCanonicalTag
}

const hasHreflang = () => {
  const technical = seoAttributes.value?.TechnicalSEOAnalyzer || {}
  return technical.hasHreflang
}

const getSeverityBadgeClasses = (severity: string) => {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800'
    case 'low':
      return 'bg-blue-100 text-blue-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

const handleSignUp = () => {
  router.push({ name: 'register', query: { source: 'trial_results' } })
}

const downloadReport = () => {
  // In real implementation, this would generate and download a PDF report
  alert('Report download would be available for registered users')
}

const shareResults = () => {
  // In real implementation, this would share the results
  const shareUrl = window.location.href
  navigator.clipboard.writeText(shareUrl)
  alert('Results link copied to clipboard!')
}

// Get category icon
const getCategoryIcon = (category: string) => {
  const icons: Record<string, string> = {
    on_page: 'file-text',
    technical: 'settings',
    content: 'edit-3',
    performance: 'zap',
    overall: 'star'
  }
  return icons[category] || 'info'
}
</script>

<template>
  <div class="results-page">
    <PublicHeader />
    
    <!-- Results Header -->
    <div class="results-header">
      <div class="results-header-container">
        <div class="results-header-content">
          <div class="results-header-left">
            <h1 class="results-title">SEO Analysis Results</h1>
            <span class="trial-badge">Free Trial</span>
          </div>
          
          <div class="results-header-actions">
            <button
              @click="shareResults"
              class="icon-button"
              title="Share results"
            >
              <i class="lucide-share-2 w-5 h-5"></i>
            </button>
            <button
              @click="downloadReport"
              class="icon-button"
              title="Download report"
            >
              <i class="lucide-download w-5 h-5"></i>
            </button>
            <button
              @click="handleSignUp"
              class="btn btn-primary"
            >
              Get Full Access
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <main class="results-container">
      <!-- Analysis Status -->
      <div v-if="trialStore.trialAnalysis" class="mb-8">
        <div class="bg-white rounded-lg shadow-sm p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h1 class="text-2xl font-bold text-gray-900 mb-2">
                SEO Analysis Results
              </h1>
              <p class="text-gray-600">
                <i class="lucide-globe w-4 h-4 inline mr-1"></i>
                {{ trialStore.trialAnalysis.url_analyzed }}
              </p>
            </div>
            <div class="text-right">
              <p class="text-sm text-gray-500">Analyzed on</p>
              <p class="text-gray-900">
                {{ new Date(trialStore.trialAnalysis.submitted_at).toLocaleString() }}
              </p>
            </div>
          </div>

          <!-- Progress indicator for ongoing analysis -->
          <div v-if="trialStore.trialAnalysis.status === 'IN_PROGRESS'" class="mt-4">
            <div class="flex items-center justify-center py-8">
              <div class="text-center">
                <i class="lucide-loader-2 w-12 h-12 text-primary-600 animate-spin mb-4"></i>
                <p class="text-lg font-medium text-gray-900">Analyzing your website...</p>
                <p class="text-gray-600 mt-2">This usually takes 30-60 seconds</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Results (shown when analysis is complete) -->
      <div v-if="trialStore.isTrialComplete" class="space-y-8">
        <!-- Overall Score -->
        <div class="bg-white rounded-lg shadow-sm p-8">
          <div class="text-center">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Overall SEO Score</h2>
            <div class="relative inline-flex items-center justify-center">
              <svg class="w-48 h-48">
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke-width="12"
                  stroke="#e5e7eb"
                  fill="none"
                />
                <circle
                  cx="96"
                  cy="96"
                  r="88"
                  stroke-width="12"
                  :stroke="overallScore >= 90 ? '#10b981' : overallScore >= 70 ? '#f59e0b' : '#ef4444'"
                  fill="none"
                  :stroke-dasharray="`${(overallScore / 100) * 553} 553`"
                  stroke-dashoffset="0"
                  stroke-linecap="round"
                  transform="rotate(-90 96 96)"
                  class="transition-all duration-1000 ease-out"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <div>
                  <div class="text-5xl font-bold" :class="getScoreColor(overallScore)">
                    {{ Math.round(overallScore) }}
                  </div>
                  <div class="text-gray-500 text-sm">out of 100</div>
                </div>
              </div>
            </div>
            <p class="mt-4 text-gray-600 max-w-2xl mx-auto">
              Your website scores {{ Math.round(overallScore) }} out of 100. 
              {{ overallScore >= 90 ? 'Excellent work!' : overallScore >= 70 ? 'Good foundation with room for improvement.' : 'Several areas need attention for better SEO performance.' }}
            </p>
          </div>
        </div>

        <!-- Category Scores -->
        <div class="bg-white rounded-lg shadow-sm p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-6">Category Breakdown</h2>
          <div class="grid md:grid-cols-2 gap-6">
            <div v-for="(data, category) in categories" :key="category" class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-gray-700 capitalize">{{ formatCategoryName(category) }}</span>
                <span class="text-sm font-bold" :class="getScoreColor(data.score)">
                  {{ Math.round(data.score) }}/100
                </span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all duration-500"
                  :class="data.score >= 90 ? 'bg-green-500' : data.score >= 70 ? 'bg-yellow-500' : 'bg-red-500'"
                  :style="`width: ${data.score}%`"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Core Web Vitals -->
        <div class="bg-white rounded-lg shadow-sm p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-6">Core Web Vitals</h2>
          <div class="grid md:grid-cols-3 gap-6">
            <div v-for="(data, metric) in coreWebVitals" :key="metric" 
                 class="border border-gray-200 rounded-lg p-4">
              <div class="flex items-start justify-between mb-2">
                <div>
                  <h3 class="font-medium text-gray-900">{{ data.label }}</h3>
                  <p class="text-2xl font-bold mt-1" :class="getStatusColor(data.status)">
                    {{ formatMetricValue(data.value, metric) }}
                  </p>
                </div>
                <i :class="[`lucide-${getStatusIcon(data.status)} w-6 h-6`, getStatusColor(data.status)]"></i>
              </div>
              <p class="text-sm text-gray-600">
                {{ data.status === 'good' ? 'Excellent' : data.status === 'warning' ? 'Needs improvement' : 'Poor' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Issues Found -->
        <div class="bg-white rounded-lg shadow-sm p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-6">Issues & Recommendations</h2>
          <div class="space-y-4">
            <div v-for="(issue, index) in issues" :key="index" 
                 class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div class="flex items-start">
                <div class="flex-shrink-0">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="getSeverityBadgeClasses(issue.severity)">
                    {{ issue.severity }}
                  </span>
                </div>
                <div class="ml-4 flex-1">
                  <h3 class="text-base font-medium text-gray-900">{{ issue.title }}</h3>
                  <p class="mt-1 text-sm text-gray-600">{{ issue.description }}</p>
                  <div class="mt-2 flex items-start">
                    <i class="lucide-lightbulb w-4 h-4 text-blue-500 mr-2 flex-shrink-0 mt-0.5"></i>
                    <p class="text-sm text-gray-700">{{ issue.recommendation }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- CTA Section -->
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white">
          <div class="text-center">
            <h2 class="text-2xl font-bold mb-4">Want to Track Your Progress?</h2>
            <p class="text-lg mb-6 text-blue-100">
              Sign up now to save your results, monitor improvements, and analyze unlimited websites.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                @click="handleSignUp"
                class="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors"
              >
                Create Free Account
              </button>
              <router-link
                to="/pricing"
                class="bg-blue-700 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-800 transition-colors"
              >
                View Pricing Plans
              </router-link>
            </div>
          </div>
        </div>

        <!-- Limited Access Notice -->
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-6">
          <div class="flex items-start">
            <i class="lucide-info w-5 h-5 text-amber-600 mr-3 flex-shrink-0 mt-0.5"></i>
            <div>
              <h3 class="text-sm font-medium text-amber-900">This is a limited trial analysis</h3>
              <p class="mt-1 text-sm text-amber-700">
                Sign up to unlock features like historical tracking, competitor analysis, 
                custom reports, and API access. Your trial results will be saved to your account.
              </p>
            </div>
          </div>
        </div>
        
        <!-- Successes Section -->
        <div v-if="successes.length > 0" class="bg-white rounded-lg shadow-sm p-6">
          <h2 class="text-lg font-medium text-gray-900 mb-6">What's Working Well</h2>
          <div class="grid md:grid-cols-2 gap-4">
            <div v-for="(success, index) in successes" :key="index" 
                 class="flex items-start p-4 bg-green-50 rounded-lg">
              <i class="lucide-check-circle w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5"></i>
              <div>
                <h3 class="text-sm font-medium text-green-900">{{ success.title }}</h3>
                <p class="mt-1 text-sm text-green-700">{{ success.description }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Advanced SEO Analytics Section -->
        <div v-if="seoAttributes" class="space-y-6">
          <!-- Content Quality Analysis -->
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-6">Content Quality Analysis</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <!-- Title & Meta Optimization -->
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <h3 class="text-sm font-medium text-gray-700">Title Optimization</h3>
                  <span class="text-xs px-2 py-1 rounded-full" 
                        :class="getTitleOptimizationClass()">
                    {{ getTitleOptimizationStatus() }}
                  </span>
                </div>
                <div class="relative">
                  <div class="flex items-center justify-center">
                    <div class="relative w-32 h-32">
                      <svg class="w-32 h-32 transform -rotate-90">
                        <circle cx="64" cy="64" r="56" stroke-width="8" stroke="#e5e7eb" fill="none" />
                        <circle cx="64" cy="64" r="56" stroke-width="8" 
                                :stroke="getTitleScore() >= 90 ? '#10b981' : getTitleScore() >= 70 ? '#f59e0b' : '#ef4444'"
                                fill="none" 
                                :stroke-dasharray="`${(getTitleScore() / 100) * 352} 352`" />
                      </svg>
                      <div class="absolute inset-0 flex items-center justify-center">
                        <div class="text-center">
                          <div class="text-2xl font-bold">{{ getTitleScore() }}%</div>
                          <div class="text-xs text-gray-500">Score</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <p class="text-xs text-gray-600 mt-2 text-center">
                    {{ metadata.titleLength || 0 }} characters
                    <span class="block text-gray-500">{{ getTitleLengthRecommendation() }}</span>
                  </p>
                </div>
              </div>

              <!-- Content Depth -->
              <div class="space-y-4">
                <h3 class="text-sm font-medium text-gray-700">Content Depth</h3>
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-gray-600">Word Count</span>
                    <span class="text-sm font-bold text-gray-900">{{ metadata.wordsCount || 0 }}</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-gray-600">Heading Structure</span>
                    <div class="flex items-center space-x-2">
                      <span v-for="i in 6" :key="i" 
                            class="text-xs px-1.5 py-0.5 rounded"
                            :class="getHeadingCount(i) > 0 ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-400'">
                        H{{ i }}:{{ getHeadingCount(i) }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-gray-600">Reading Ease</span>
                    <span class="text-sm font-bold" :class="getReadabilityColor()">
                      {{ getReadabilityScore() }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Keyword Analysis -->
              <div class="space-y-4">
                <h3 class="text-sm font-medium text-gray-700">Top Keywords</h3>
                <div class="flex flex-wrap gap-2">
                  <span v-for="keyword in topKeywords" :key="keyword.keyword"
                        class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        :style="`font-size: ${getKeywordSize(keyword.count)}px`">
                    {{ keyword.keyword }} ({{ keyword.count }})
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Technical SEO Performance -->
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-6">Technical SEO Performance</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <!-- Page Speed -->
              <div class="text-center">
                <div class="relative inline-flex items-center justify-center">
                  <svg class="w-24 h-24">
                    <circle cx="48" cy="48" r="40" stroke-width="6" stroke="#e5e7eb" fill="none" />
                    <circle cx="48" cy="48" r="40" stroke-width="6" 
                            :stroke="getSpeedScoreColor()" 
                            fill="none"
                            :stroke-dasharray="`${(getSpeedScore() / 100) * 251} 251`"
                            stroke-linecap="round"
                            transform="rotate(-90 48 48)" />
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <div class="text-xs">
                      <i class="lucide-zap w-6 h-6" :class="getSpeedScoreColor()"></i>
                    </div>
                  </div>
                </div>
                <h4 class="text-sm font-medium text-gray-900 mt-2">Page Speed</h4>
                <p class="text-xs text-gray-600">{{ getTTFB() }}s TTFB</p>
                <p class="text-xs" :class="getSpeedScoreTextColor()">{{ getSpeedStatus() }}</p>
              </div>

              <!-- Mobile Optimization -->
              <div class="text-center">
                <div class="relative inline-flex items-center justify-center">
                  <div class="w-24 h-24 rounded-full flex items-center justify-center"
                       :class="getMobileOptimizationBg()">
                    <i class="lucide-smartphone w-8 h-8" :class="getMobileOptimizationColor()"></i>
                  </div>
                </div>
                <h4 class="text-sm font-medium text-gray-900 mt-2">Mobile Ready</h4>
                <p class="text-xs text-gray-600">{{ getMobileScore() }}% optimized</p>
                <p class="text-xs" :class="getMobileOptimizationTextColor()">{{ getMobileStatus() }}</p>
              </div>

              <!-- Security Score -->
              <div class="text-center">
                <div class="relative inline-flex items-center justify-center">
                  <div class="w-24 h-24 rounded-full flex items-center justify-center"
                       :class="getSecurityBg()">
                    <i class="lucide-shield-check w-8 h-8" :class="getSecurityColor()"></i>
                  </div>
                </div>
                <h4 class="text-sm font-medium text-gray-900 mt-2">Security</h4>
                <p class="text-xs text-gray-600">{{ getSecurityFeatures() }} features</p>
                <p class="text-xs" :class="getSecurityTextColor()">{{ getSecurityStatus() }}</p>
              </div>

              <!-- Crawlability -->
              <div class="text-center">
                <div class="relative inline-flex items-center justify-center">
                  <div class="w-24 h-24 rounded-full flex items-center justify-center"
                       :class="getCrawlabilityBg()">
                    <i class="lucide-bot w-8 h-8" :class="getCrawlabilityColor()"></i>
                  </div>
                </div>
                <h4 class="text-sm font-medium text-gray-900 mt-2">Crawlability</h4>
                <p class="text-xs text-gray-600">{{ getCrawlabilityScore() }}% ready</p>
                <p class="text-xs" :class="getCrawlabilityTextColor()">{{ getCrawlabilityStatus() }}</p>
              </div>
            </div>
          </div>

          <!-- Link Profile & Modern Features -->
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Link Profile -->
            <div class="bg-white rounded-lg shadow-sm p-6">
              <h3 class="text-sm font-medium text-gray-900 mb-4">Link Profile</h3>
              <div class="space-y-4">
                <div class="relative h-32">
                  <div class="absolute inset-0 flex items-center justify-center">
                    <div class="grid grid-cols-2 gap-4 text-center">
                      <div>
                        <div class="text-2xl font-bold text-blue-600">{{ getInternalLinksCount() }}</div>
                        <div class="text-xs text-gray-600">Internal</div>
                      </div>
                      <div>
                        <div class="text-2xl font-bold text-purple-600">{{ getExternalLinksCount() }}</div>
                        <div class="text-xs text-gray-600">External</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-if="getBrokenLinksCount() > 0" class="flex items-center justify-between p-3 bg-red-50 rounded">
                  <span class="text-sm text-red-700">Broken Links Found</span>
                  <span class="text-sm font-bold text-red-700">{{ getBrokenLinksCount() }}</span>
                </div>
              </div>
            </div>

            <!-- Modern SEO Features -->
            <div class="bg-white rounded-lg shadow-sm p-6">
              <h3 class="text-sm font-medium text-gray-900 mb-4">Modern SEO Features</h3>
              <div class="grid grid-cols-2 gap-3">
                <div class="flex items-center justify-between p-3 rounded-lg"
                     :class="hasStructuredData() ? 'bg-green-50' : 'bg-gray-50'">
                  <span class="text-xs text-gray-700">Structured Data</span>
                  <i :class="[hasStructuredData() ? 'lucide-check text-green-600' : 'lucide-x text-gray-400', 'w-4 h-4']"></i>
                </div>
                <div class="flex items-center justify-between p-3 rounded-lg"
                     :class="hasModernImageFormats() ? 'bg-green-50' : 'bg-gray-50'">
                  <span class="text-xs text-gray-700">WebP/AVIF</span>
                  <i :class="[hasModernImageFormats() ? 'lucide-check text-green-600' : 'lucide-x text-gray-400', 'w-4 h-4']"></i>
                </div>
                <div class="flex items-center justify-between p-3 rounded-lg"
                     :class="hasCanonicalTag() ? 'bg-green-50' : 'bg-gray-50'">
                  <span class="text-xs text-gray-700">Canonical Tag</span>
                  <i :class="[hasCanonicalTag() ? 'lucide-check text-green-600' : 'lucide-x text-gray-400', 'w-4 h-4']"></i>
                </div>
                <div class="flex items-center justify-between p-3 rounded-lg"
                     :class="hasHreflang() ? 'bg-green-50' : 'bg-gray-50'">
                  <span class="text-xs text-gray-700">Hreflang</span>
                  <i :class="[hasHreflang() ? 'lucide-check text-green-600' : 'lucide-x text-gray-400', 'w-4 h-4']"></i>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.results-page {
  min-height: 100vh;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

.results-header {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.results-header-container {
  max-width: 80rem;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.results-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.results-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.trial-badge {
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-full);
}

.results-header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.icon-button {
  padding: var(--spacing-sm);
  background-color: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-button:hover {
  background-color: var(--color-surface-variant);
  color: var(--color-text-primary);
}

/* Main content styles */
.results-container {
  max-width: 80rem;
  margin: 0 auto;
  padding: var(--spacing-2xl) var(--spacing-lg);
}

/* Update all background and text colors */
.bg-white {
  background-color: var(--color-surface);
}

.bg-gray-50 {
  background-color: var(--color-surface-variant);
}

.bg-gray-100 {
  background-color: var(--color-surface-variant);
}

.text-gray-900 {
  color: var(--color-text-primary);
}

.text-gray-800 {
  color: var(--color-text-primary);
}

.text-gray-700 {
  color: var(--color-text-primary);
}

.text-gray-600 {
  color: var(--color-text-secondary);
}

.text-gray-500 {
  color: var(--color-text-tertiary);
}

.border-gray-200 {
  border-color: var(--color-border);
}

.border-gray-300 {
  border-color: var(--color-border);
}

/* Card styles */
.card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

/* Score circle */
.score-circle {
  background-color: var(--color-surface);
  border: 8px solid var(--color-surface-variant);
}

/* Status badges with theme support */
.bg-green-100 {
  background-color: rgba(65, 192, 93, 0.1);
}

.text-green-800 {
  color: var(--color-secondary);
}

.bg-yellow-100 {
  background-color: rgba(253, 214, 99, 0.1);
}

.text-yellow-800 {
  color: var(--color-accent);
}

.bg-red-100 {
  background-color: rgba(242, 139, 130, 0.1);
}

.text-red-800 {
  color: var(--color-danger);
}

.bg-blue-100 {
  background-color: rgba(66, 133, 244, 0.1);
}

.text-blue-800 {
  color: var(--color-primary);
}

/* Progress bars */
.bg-gray-200 {
  background-color: var(--color-surface-variant);
}

/* Hover states */
.hover\:bg-gray-100:hover {
  background-color: var(--color-surface-variant);
}

.hover\:text-gray-900:hover {
  color: var(--color-text-primary);
}

/* Issue and success items */
.issue-item,
.success-item {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
}

/* Custom animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.5s ease-out;
}
</style>