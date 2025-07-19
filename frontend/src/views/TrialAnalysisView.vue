<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTrialStore } from '@/stores/trial'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import PublicHeader from '@/components/layout/PublicHeader.vue'

const router = useRouter()
const trialStore = useTrialStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

const form = reactive({
  url: ''
})

const errors = reactive({
  url: '',
  general: ''
})

const isValidUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`)
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

const validateForm = () => {
  errors.url = ''
  errors.general = ''
  
  if (!form.url.trim()) {
    errors.url = 'Please enter a URL to analyze'
    return false
  }
  
  if (!isValidUrl(form.url.trim())) {
    errors.url = 'Please enter a valid URL'
    return false
  }
  
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return
  
  // Clear any previous errors
  errors.general = ''
  
  // Ensure URL has protocol
  const url = form.url.startsWith('http') ? form.url : `https://${form.url}`
  
  const result = await trialStore.submitTrialAnalysis(url)
  
  if (result) {
    // Redirect to trial results page
    router.push({
      name: 'trial-results',
      params: { id: result.id }
    })
  } else if (trialStore.error) {
    errors.general = trialStore.error
  }
}

const handleSignUp = () => {
  router.push({ name: 'register' })
}

const handleLogin = () => {
  router.push({ name: 'login' })
}

// Watch for trial store errors
watch(() => trialStore.error, (newError) => {
  if (newError) {
    errors.general = newError
  }
})

// Sample URLs for demo
const sampleUrls = [
  'example.com',
  'mybusiness.com',
  'myportfolio.com'
]

const loadSampleUrl = (url: string) => {
  form.url = url
  errors.url = ''
}
</script>

<template>
  <div class="trial-page">
    <PublicHeader />

    <!-- Main Content -->
    <main class="trial-container">
      <!-- Hero Section -->
      <div class="trial-hero">
        <h1 class="trial-title">
          Try Core Website Vitals
          <span class="gradient-text"> Free</span>
        </h1>
        <p class="trial-subtitle">
          Get a comprehensive SEO analysis of your website instantly. No sign-up required for your first analysis.
        </p>
      </div>

      <!-- Trial Form -->
      <div class="trial-form-card">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- URL Input -->
          <div>
            <label for="url" class="block text-sm font-medium text-gray-700 mb-2">
              Enter Your Website URL
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <i class="lucide-globe w-5 h-5 text-gray-400"></i>
              </div>
              <input
                id="url"
                v-model="form.url"
                type="text"
                :disabled="trialStore.isSubmitting"
                class="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                :class="{ 
                  'border-red-300 focus:ring-red-500': errors.url,
                  'opacity-50 cursor-not-allowed': trialStore.isSubmitting
                }"
                placeholder="www.example.com"
                @input="errors.url = ''"
              />
            </div>
            <div v-if="errors.url" class="mt-2 text-sm text-red-600 flex items-center">
              <i class="lucide-alert-circle w-4 h-4 mr-1"></i>
              {{ errors.url }}
            </div>
            
            <!-- Sample URLs -->
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <span class="text-sm text-gray-500">Try:</span>
              <button
                v-for="url in sampleUrls"
                :key="url"
                type="button"
                @click="loadSampleUrl(url)"
                class="text-sm text-blue-600 hover:text-blue-700 hover:underline transition-colors"
              >
                {{ url }}
              </button>
            </div>
          </div>

          <!-- Features List -->
          <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
            <h3 class="text-sm font-semibold text-gray-900 mb-3">Your free analysis includes:</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="flex items-center text-sm text-gray-700">
                <i class="lucide-check-circle w-5 h-5 text-green-500 mr-2 flex-shrink-0"></i>
                SEO Score & Recommendations
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <i class="lucide-check-circle w-5 h-5 text-green-500 mr-2 flex-shrink-0"></i>
                Core Web Vitals Analysis
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <i class="lucide-check-circle w-5 h-5 text-green-500 mr-2 flex-shrink-0"></i>
                Technical SEO Audit
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <i class="lucide-check-circle w-5 h-5 text-green-500 mr-2 flex-shrink-0"></i>
                Content Optimization Tips
              </div>
            </div>
          </div>

          <!-- Error Message -->
          <div v-if="errors.general" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <div class="flex items-start">
              <i class="lucide-alert-circle w-5 h-5 text-red-400 mr-2 flex-shrink-0 mt-0.5"></i>
              <div>
                <h3 class="text-sm font-medium text-red-800">Analysis Error</h3>
                <p class="mt-1 text-sm text-red-700">{{ errors.general }}</p>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="trialStore.isSubmitting || !trialStore.canUseTrial"
            class="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-6 rounded-lg font-medium text-lg hover:shadow-lg transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            <span v-if="trialStore.isSubmitting" class="flex items-center justify-center">
              <i class="lucide-loader-2 w-5 h-5 mr-2 animate-spin"></i>
              Analyzing Your Website...
            </span>
            <span v-else-if="!trialStore.canUseTrial">
              Trial Already Used
            </span>
            <span v-else class="flex items-center justify-center">
              <i class="lucide-search w-5 h-5 mr-2"></i>
              Analyze My Website Free
            </span>
          </button>

          <!-- Trial Notice -->
          <p class="text-center text-sm text-gray-500">
            No credit card required • Results in 60 seconds
          </p>
        </form>
      </div>

      <!-- Already Used Trial -->
      <div v-if="!trialStore.canUseTrial && trialStore.trialAnalysis" class="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-8">
        <div class="flex items-start">
          <i class="lucide-info w-5 h-5 text-amber-600 mr-3 flex-shrink-0 mt-0.5"></i>
          <div class="flex-1">
            <h3 class="text-sm font-medium text-amber-900">You've already used your free trial</h3>
            <p class="mt-1 text-sm text-amber-700">
              You analyzed <strong>{{ trialStore.trialAnalysis.url_analyzed }}</strong> on 
              {{ new Date(trialStore.trialAnalysis.submitted_at).toLocaleDateString() }}.
            </p>
            <div class="mt-3 flex flex-col sm:flex-row gap-3">
              <router-link
                :to="{ name: 'trial-results', params: { id: trialStore.trialAnalysis.id } }"
                class="inline-flex items-center justify-center px-4 py-2 border border-amber-600 text-sm font-medium rounded-md text-amber-700 bg-white hover:bg-amber-50 transition-colors"
              >
                View Previous Results
              </router-link>
              <button
                @click="handleSignUp"
                class="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-amber-600 hover:bg-amber-700 transition-colors"
              >
                Sign Up for Unlimited Analyses
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Benefits Section -->
      <div class="grid md:grid-cols-3 gap-6 mb-12">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mb-4">
            <i class="lucide-zap w-6 h-6 text-blue-600"></i>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Lightning Fast</h3>
          <p class="text-gray-600">Get comprehensive results in under 60 seconds</p>
        </div>
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-12 h-12 bg-purple-100 rounded-full mb-4">
            <i class="lucide-shield-check w-6 h-6 text-purple-600"></i>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No Sign-up Required</h3>
          <p class="text-gray-600">Try before you commit, no strings attached</p>
        </div>
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4">
            <i class="lucide-trending-up w-6 h-6 text-green-600"></i>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Actionable Insights</h3>
          <p class="text-gray-600">Clear recommendations to improve your SEO</p>
        </div>
      </div>

      <!-- FAQ Section -->
      <div class="bg-gray-50 rounded-2xl p-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">Frequently Asked Questions</h2>
        <div class="space-y-6 max-w-2xl mx-auto">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">What's included in the free trial?</h3>
            <p class="text-gray-600">You get a complete SEO analysis including technical audit, content analysis, performance metrics, and actionable recommendations.</p>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">Do I need to provide credit card details?</h3>
            <p class="text-gray-600">No! The trial is completely free with no credit card required. Sign up only when you're ready for unlimited analyses.</p>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-2">How many sites can I analyze for free?</h3>
            <p class="text-gray-600">You can analyze one website for free. Create an account to analyze unlimited websites and track progress over time.</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.trial-page {
  min-height: 100vh;
  background-color: var(--color-background);
  color: var(--color-text-primary);
  transition: background-color var(--transition-base), color var(--transition-base);
}

.trial-container {
  max-width: 64rem;
  margin: 0 auto;
  padding: 4rem var(--spacing-lg);
}

.trial-hero {
  text-align: center;
  margin-bottom: var(--spacing-3xl);
}

.trial-title {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

@media (min-width: 768px) {
  .trial-title {
    font-size: 3.75rem;
  }
}

.gradient-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.trial-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  max-width: 48rem;
  margin: 0 auto;
}

.trial-form-card {
  background-color: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-2xl);
  margin-bottom: var(--spacing-2xl);
  border: 1px solid var(--color-border);
}

/* Update form input styles */
.form-input {
  background-color: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.form-input:focus {
  border-color: var(--color-primary);
  background-color: var(--color-surface);
}

/* Update label styles */
label {
  color: var(--color-text-primary);
}

/* Features section */
.features-grid {
  background-color: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--spacing-2xl);
  border: 1px solid var(--color-border);
}

.feature-item {
  background-color: var(--color-surface-variant);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Update text colors */
.text-gray-900 {
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

/* Background colors */
.bg-white {
  background-color: var(--color-surface);
}

.bg-gray-50 {
  background-color: var(--color-surface-variant);
}

/* Loading spinner */
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

@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

.bg-gradient-to-r {
  background-size: 200% auto;
  animation: gradient-shift 3s ease infinite;
}
</style>