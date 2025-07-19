<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAnalysisStore } from '@/stores/analysis'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { Line, Doughnut, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
  Filler
)

const authStore = useAuthStore()
const analysisStore = useAnalysisStore()
const router = useRouter()

onMounted(async () => {
  // Redirect to login if not authenticated
  if (!authStore.isAuthenticated) {
    router.push({ name: 'login' })
    return
  }
  
  // Fetch user's analyses
  await analysisStore.fetchAnalyses(true)
  
  // Subscribe to real-time updates
  if (authStore.user?.id) {
    analysisStore.subscribeToRealTimeUpdates(authStore.user.id)
  }
})

const startNewAnalysis = () => {
  router.push({ name: 'analysis' })
}

const viewAnalysisHistory = () => {
  router.push({ name: 'analysis-history' })
}

const viewAnalysisResult = (analysisId: string) => {
  router.push({ name: 'analysis-result', params: { id: analysisId } })
}

// Chart data computed properties
const performanceTrendData = computed(() => {
  const last30Days = Array.from({ length: 30 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - 29 + i)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  })
  
  const scores = Array.from({ length: 30 }, () => Math.floor(Math.random() * 40) + 60)
  
  return {
    labels: last30Days,
    datasets: [
      {
        label: 'Average SEO Score',
        data: scores,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  }
})

const analysisStatusData = computed(() => {
  const stats = analysisStore.analysisStats
  return {
    labels: ['Completed', 'In Progress', 'Failed', 'Pending'],
    datasets: [
      {
        data: [stats.completed, stats.inProgress, stats.failed, stats.pending],
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6b7280'],
        borderWidth: 0,
      },
    ],
  }
})

const topIssuesData = computed(() => {
  const issues = [
    { name: 'Missing Meta Description', count: 15 },
    { name: 'Slow Page Load', count: 12 },
    { name: 'Missing Alt Text', count: 8 },
    { name: 'Duplicate Title Tags', count: 6 },
    { name: 'Poor Mobile Experience', count: 4 },
  ]
  
  return {
    labels: issues.map(issue => issue.name),
    datasets: [
      {
        label: 'Issues Found',
        data: issues.map(issue => issue.count),
        backgroundColor: [
          '#ef4444',
          '#f59e0b',
          '#8b5cf6',
          '#06b6d4',
          '#84cc16',
        ],
        borderWidth: 0,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom' as const,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
}
</script>

<template>
  <AppLayout>
    <div class="dashboard-view">
      <!-- Page Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">
            {{ $t('dashboard.title') }}
          </h1>
          <p class="page-subtitle">
            {{ $t('dashboard.welcome', { name: authStore.userName }) }}
          </p>
        </div>
        
        <div class="page-actions">
          <button
            @click="startNewAnalysis"
            class="btn btn-primary"
          >
            <i class="lucide-plus w-4 h-4 mr-2"></i>
            {{ $t('analysis.new_analysis') }}
          </button>
          
          <button
            @click="viewAnalysisHistory"
            class="btn btn-outline"
          >
            <i class="lucide-history w-4 h-4 mr-2"></i>
            {{ $t('navigation.history') }}
          </button>
        </div>
      </div>

      <!-- Dashboard Content -->
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="card">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">
                  {{ $t('dashboard.summary.total_analyses') }}
                </p>
                <p class="text-2xl font-bold text-gray-900">
                  {{ analysisStore.analysisStats.total }}
                </p>
              </div>
              <div class="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg">
                <i class="lucide-search w-6 h-6 text-blue-600"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">
                  {{ $t('dashboard.summary.pending_analyses') }}
                </p>
                <p class="text-2xl font-bold text-gray-900">
                  {{ analysisStore.analysisStats.pending + analysisStore.analysisStats.inProgress }}
                </p>
              </div>
              <div class="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-lg">
                <i class="lucide-clock w-6 h-6 text-yellow-600"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">
                  {{ $t('dashboard.summary.average_score') }}
                </p>
                <p class="text-2xl font-bold text-gray-900">
                  {{ Math.round(analysisStore.analysisStats.successRate) }}%
                </p>
              </div>
              <div class="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg">
                <i class="lucide-trending-up w-6 h-6 text-green-600"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div class="card">
          <div class="card-body">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">
                  {{ $t('dashboard.summary.improvement') }}
                </p>
                <p class="text-2xl font-bold text-gray-900">
                  +{{ analysisStore.analysisStats.completed }}
                </p>
              </div>
              <div class="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg">
                <i class="lucide-bar-chart w-6 h-6 text-purple-600"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Analyses -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2">
          <div class="card">
            <div class="card-header">
              <h2 class="text-lg font-medium text-gray-900">
                {{ $t('dashboard.recent_analyses.title') }}
              </h2>
            </div>
            <div class="card-body">
              <div v-if="analysisStore.recentAnalyses.length === 0" class="text-center py-8">
                <i class="lucide-search w-12 h-12 text-gray-400 mx-auto mb-4"></i>
                <p class="text-gray-500">
                  {{ $t('dashboard.recent_analyses.no_analyses') }}
                </p>
                <button
                  @click="startNewAnalysis"
                  class="btn btn-primary mt-4"
                >
                  {{ $t('analysis.new_analysis') }}
                </button>
              </div>
              
              <div v-else class="space-y-4">
                <div
                  v-for="analysis in analysisStore.recentAnalyses.slice(0, 5)"
                  :key="analysis.id"
                  class="analysis-item"
                  @click="viewAnalysisResult(analysis.id)"
                >
                  <div class="flex items-center space-x-3">
                    <div class="flex-shrink-0">
                      <i
                        :class="[
                          'w-5 h-5',
                          analysis.status === 'SUCCESS' ? 'text-green-600' : 
                          analysis.status === 'FAILED' ? 'text-red-600' : 
                          analysis.status === 'IN_PROGRESS' ? 'text-blue-600' : 
                          'text-yellow-600'
                        ]"
                        :name="analysisStore.getStatusIcon(analysis.status)"
                      ></i>
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900">
                        {{ analysis.url_analyzed }}
                      </p>
                      <p class="text-xs text-gray-500">
                        {{ new Date(analysis.submitted_at).toLocaleDateString() }}
                      </p>
                    </div>
                  </div>
                  
                  <div class="flex items-center space-x-2">
                    <span
                      :class="[
                        'badge',
                        analysisStore.getStatusColor(analysis.status)
                      ]"
                    >
                      {{ $t(`analysis.status.${analysis.status}`) }}
                    </span>
                    <i class="lucide-chevron-right w-4 h-4 text-gray-400"></i>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="analysisStore.recentAnalyses.length > 5" class="card-footer">
              <button
                @click="viewAnalysisHistory"
                class="btn btn-outline w-full"
              >
                {{ $t('dashboard.recent_analyses.view_all') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="space-y-6">
          <div class="card">
            <div class="card-header">
              <h2 class="text-lg font-medium text-gray-900">
                {{ $t('dashboard.quick_actions.title') }}
              </h2>
            </div>
            <div class="card-body space-y-4">
              <button
                @click="startNewAnalysis"
                class="btn btn-primary w-full"
              >
                <i class="lucide-plus w-4 h-4 mr-2"></i>
                {{ $t('dashboard.quick_actions.new_analysis') }}
              </button>
              
              <button
                @click="viewAnalysisHistory"
                class="btn btn-outline w-full"
              >
                <i class="lucide-file-text w-4 h-4 mr-2"></i>
                {{ $t('dashboard.quick_actions.view_reports') }}
              </button>
              
              <button
                @click="$router.push({ name: 'billing' })"
                class="btn btn-outline w-full"
              >
                <i class="lucide-star w-4 h-4 mr-2"></i>
                {{ $t('dashboard.quick_actions.upgrade_plan') }}
              </button>
            </div>
          </div>
          
          <!-- Subscription Info -->
          <div class="card">
            <div class="card-header">
              <h2 class="text-lg font-medium text-gray-900">
                {{ $t('profile.subscription') }}
              </h2>
            </div>
            <div class="card-body">
              <div class="text-center">
                <p class="text-sm text-gray-600 mb-2">
                  {{ $t('billing.current_plan') }}
                </p>
                <p class="text-lg font-semibold text-primary-600 capitalize">
                  {{ authStore.subscriptionTier }}
                </p>
                <button
                  v-if="authStore.subscriptionTier === 'free'"
                  @click="$router.push({ name: 'billing' })"
                  class="btn btn-primary btn-sm mt-3"
                >
                  {{ $t('billing.upgrade') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Analytics Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
        <!-- Performance Trend Chart -->
        <div class="lg:col-span-2 card">
          <div class="card-header">
            <h2 class="text-lg font-medium text-gray-900">
              Performance Trend (Last 30 Days)
            </h2>
          </div>
          <div class="card-body">
            <div class="h-80">
              <Line 
                :data="performanceTrendData" 
                :options="chartOptions" 
              />
            </div>
          </div>
        </div>

        <!-- Analysis Status Distribution -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-medium text-gray-900">
              Analysis Status
            </h2>
          </div>
          <div class="card-body">
            <div class="h-64">
              <Doughnut 
                :data="analysisStatusData" 
                :options="{ ...chartOptions, scales: undefined }" 
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Top Issues Chart -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-medium text-gray-900">
              Most Common Issues
            </h2>
          </div>
          <div class="card-body">
            <div class="h-64">
              <Bar 
                :data="topIssuesData" 
                :options="chartOptions" 
              />
            </div>
          </div>
        </div>

        <!-- Performance Insights -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-medium text-gray-900">
              Performance Insights
            </h2>
          </div>
          <div class="card-body">
            <div class="space-y-6">
              <!-- Core Web Vitals -->
              <div>
                <h3 class="text-sm font-medium text-gray-700 mb-3">Core Web Vitals</h3>
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">LCP (Largest Contentful Paint)</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-16 bg-gray-200 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: 75%"></div>
                      </div>
                      <span class="text-sm text-green-600 font-medium">2.1s</span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">FID (First Input Delay)</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-16 bg-gray-200 rounded-full h-2">
                        <div class="bg-yellow-500 h-2 rounded-full" style="width: 60%"></div>
                      </div>
                      <span class="text-sm text-yellow-600 font-medium">120ms</span>
                    </div>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">CLS (Cumulative Layout Shift)</span>
                    <div class="flex items-center space-x-2">
                      <div class="w-16 bg-gray-200 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: 85%"></div>
                      </div>
                      <span class="text-sm text-green-600 font-medium">0.08</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- SEO Health Score -->
              <div>
                <h3 class="text-sm font-medium text-gray-700 mb-3">SEO Health Score</h3>
                <div class="flex items-center justify-center">
                  <div class="relative w-24 h-24">
                    <svg class="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#e5e7eb"
                        stroke-width="2"
                        stroke-dasharray="100, 100"
                      />
                      <path
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#3b82f6"
                        stroke-width="2"
                        stroke-dasharray="82, 100"
                      />
                    </svg>
                    <div class="absolute inset-0 flex items-center justify-center">
                      <span class="text-xl font-bold text-gray-900">82%</span>
                    </div>
                  </div>
                </div>
                <p class="text-center text-sm text-gray-600 mt-2">
                  Good - Keep improving!
                </p>
              </div>

              <!-- Quick Tips -->
              <div>
                <h3 class="text-sm font-medium text-gray-700 mb-3">Quick Tips</h3>
                <ul class="space-y-2 text-sm text-gray-600">
                  <li class="flex items-start space-x-2">
                    <i class="lucide-check-circle w-4 h-4 text-green-500 mt-0.5"></i>
                    <span>Add meta descriptions to improve CTR</span>
                  </li>
                  <li class="flex items-start space-x-2">
                    <i class="lucide-check-circle w-4 h-4 text-green-500 mt-0.5"></i>
                    <span>Optimize images for faster loading</span>
                  </li>
                  <li class="flex items-start space-x-2">
                    <i class="lucide-check-circle w-4 h-4 text-green-500 mt-0.5"></i>
                    <span>Fix broken internal links</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.dashboard-view {
  padding: var(--spacing-xl) 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2xl);
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs) 0;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.page-actions {
  display: flex;
  gap: var(--spacing-md);
}

/* Analysis item */
.analysis-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.analysis-item:hover {
  background-color: var(--color-surface-variant);
}

/* Custom hover effects */
.hover\:bg-gray-100:hover {
  background-color: var(--color-surface-variant);
  transition: background-color 0.2s ease-in-out;
}

/* Loading state for stats */
.card-body .text-2xl {
  min-height: 2rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .grid-cols-1.md\:grid-cols-4 {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>