<template>
  <section class="hero-section relative overflow-hidden">
    <!-- Background gradient with animation -->
    <div class="hero-background">
      <div class="hero-pattern"></div>
    </div>
    
    <!-- Content -->
    <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
      <div class="grid lg:grid-cols-2 gap-12 items-center">
        <!-- Text content -->
        <div class="text-center lg:text-left">
          <h1 class="hero-title animate-fade-in">
            Analyze Your Website's
            <span class="hero-title-accent">
              SEO Performance
            </span>
          </h1>
          
          <p class="hero-subtitle animate-fade-in animation-delay-200">
            Get comprehensive SEO insights, Core Web Vitals monitoring, and actionable recommendations to boost your search rankings.
          </p>
          
          <div class="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start animate-fade-in animation-delay-400">
            <button
              @click="$emit('try-free')"
              class="hero-button-primary"
            >
              <SearchIcon class="w-5 h-5 mr-2" />
              Try It Free - No Sign Up
            </button>
            
            <button
              @click="$emit('login')"
              class="hero-button-secondary"
            >
              Sign In
              <ArrowRightIcon class="w-5 h-5 ml-2" />
            </button>
          </div>
        </div>
        
        <!-- Performance metrics visualization -->
        <div class="relative animate-fade-in animation-delay-600">
          <div class="hero-metrics-card">
            <!-- Metrics header -->
            <div class="flex items-center justify-between mb-6">
              <h3 class="hero-metrics-title">Live Performance Metrics</h3>
              <span class="hero-metrics-badge">
                <span class="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Real-time
              </span>
            </div>
            
            <!-- Core Web Vitals -->
            <div class="space-y-6">
              <MetricCard
                v-for="metric in metrics"
                :key="metric.name"
                :metric="metric"
                :class="`animate-fade-in animation-delay-${800 + metric.delay}`"
              />
            </div>
            
            <!-- SEO Score -->
            <div class="mt-8 pt-6 score-section-divider">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm metric-label">Overall SEO Score</p>
                  <p class="text-3xl font-bold metric-value mt-1">{{ animatedScore }}%</p>
                </div>
                <div class="relative w-24 h-24">
                  <svg class="transform -rotate-90 w-24 h-24">
                    <circle
                      cx="48"
                      cy="48"
                      r="36"
                      stroke="currentColor"
                      stroke-width="8"
                      fill="none"
                      class="score-circle-background"
                    />
                    <circle
                      cx="48"
                      cy="48"
                      r="36"
                      stroke="currentColor"
                      stroke-width="8"
                      fill="none"
                      :stroke-dasharray="`${circumference} ${circumference}`"
                      :stroke-dashoffset="strokeDashoffset"
                      class="score-circle-stroke transition-all duration-1000 ease-out"
                      stroke-linecap="round"
                    />
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <TrendingUpIcon class="w-8 h-8 score-icon" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Floating badges -->
          <div class="absolute -top-4 -right-4 floating-badge badge-accent animate-bounce">
            Free Trial
          </div>
          
          <div class="absolute -bottom-6 -left-6 floating-badge badge-light flex items-center space-x-2">
            <CheckIcon class="w-5 h-5 text-green-500" />
            <span>No Credit Card Required</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SearchIcon from '@/components/icons/SearchIcon.vue'
import ArrowRightIcon from '@/components/icons/ArrowRightIcon.vue'
import TrendingUpIcon from '@/components/icons/TrendingUpIcon.vue'
import CheckIcon from '@/components/icons/CheckIcon.vue'
import MetricCard from './MetricCard.vue'

defineEmits<{
  'try-free': []
  'login': []
}>()

// Animated SEO score
const targetScore = 92
const animatedScore = ref(0)
const circumference = 2 * Math.PI * 36

const strokeDashoffset = computed(() => {
  const offset = circumference - (animatedScore.value / 100) * circumference
  return offset
})

// Performance metrics
const metrics = ref([
  {
    name: 'LCP',
    label: 'Largest Contentful Paint',
    value: 2.4,
    unit: 's',
    status: 'good',
    threshold: 2.5,
    delay: 0
  },
  {
    name: 'FID',
    label: 'First Input Delay',
    value: 45,
    unit: 'ms',
    status: 'good',
    threshold: 100,
    delay: 100
  },
  {
    name: 'CLS',
    label: 'Cumulative Layout Shift',
    value: 0.08,
    unit: '',
    status: 'good',
    threshold: 0.1,
    delay: 200
  }
])

onMounted(() => {
  // Animate score counting up
  const interval = setInterval(() => {
    if (animatedScore.value < targetScore) {
      animatedScore.value += 1
    } else {
      clearInterval(interval)
    }
  }, 20)
  
  // Simulate real-time metric updates
  setInterval(() => {
    metrics.value.forEach(metric => {
      // Add small random fluctuations
      const fluctuation = (Math.random() - 0.5) * 0.1
      const baseValue = metric.name === 'LCP' ? 2.4 : metric.name === 'FID' ? 45 : 0.08
      metric.value = Number((baseValue + fluctuation * baseValue).toFixed(2))
    })
  }, 3000)
})
</script>

<style scoped>
/* Hero section background */
.hero-section {
  background-color: var(--color-background);
}

/* Light mode background */
[data-theme="light"] .hero-background {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Dark mode background */
[data-theme="dark"] .hero-background,
:root:not([data-theme="light"]) .hero-background {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    rgba(66, 133, 244, 0.1) 0%, 
    rgba(26, 115, 232, 0.1) 50%, 
    rgba(66, 133, 244, 0.1) 100%
  );
}

/* Pattern overlay */
.hero-pattern {
  position: absolute;
  inset: 0;
  opacity: 0.1;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* Text styles */
.hero-title {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

@media (min-width: 768px) {
  .hero-title {
    font-size: 3rem;
  }
}

@media (min-width: 1024px) {
  .hero-title {
    font-size: 3.75rem;
  }
}

.hero-title-accent {
  display: block;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: 2rem;
}

/* Button styles */
.hero-button-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 2rem;
  font-size: 1.125rem;
  font-weight: 500;
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  transform: translateY(0);
}

.hero-button-primary:hover {
  background-color: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.hero-button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 2rem;
  font-size: 1.125rem;
  font-weight: 500;
  background-color: transparent;
  color: var(--color-text-primary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.hero-button-secondary:hover {
  background-color: var(--color-surface);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Metrics card */
.hero-metrics-card {
  position: relative;
  background-color: var(--color-surface);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: var(--radius-xl);
  padding: 2rem;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xl);
}

[data-theme="dark"] .hero-metrics-card {
  background-color: rgba(41, 42, 45, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.hero-metrics-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.hero-metrics-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  background-color: rgba(65, 192, 93, 0.1);
  color: var(--color-secondary);
  border: 1px solid rgba(65, 192, 93, 0.3);
}

/* Update metric text colors */
.metric-label {
  color: var(--color-text-secondary);
}

.metric-value {
  color: var(--color-text-primary);
}

.metric-status {
  color: var(--color-secondary);
}

/* Overall score styling */
.score-circle {
  background-color: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.score-label {
  color: var(--color-text-secondary);
}

.score-circle-stroke {
  color: var(--color-primary);
}

.score-icon {
  color: var(--color-text-primary);
}

/* Floating badges */
.floating-badge {
  font-weight: 500;
  font-size: 0.875rem;
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-full);
  padding: 0.5rem 1rem;
}

.badge-accent {
  background-color: var(--color-accent);
  color: var(--color-primary);
}

.badge-light {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-lg);
}

/* Score section styling */
.score-section-divider {
  border-top: 1px solid rgba(156, 163, 175, 0.3);
}

[data-theme="dark"] .score-section-divider {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.score-circle-background {
  color: rgba(156, 163, 175, 0.5);
}

[data-theme="dark"] .score-circle-background {
  color: rgba(255, 255, 255, 0.2);
}

/* Animation utilities */
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.8s ease-out forwards;
  opacity: 0;
}

.animation-delay-200 {
  animation-delay: 200ms;
}

.animation-delay-400 {
  animation-delay: 400ms;
}

.animation-delay-600 {
  animation-delay: 600ms;
}

.animation-delay-800 {
  animation-delay: 800ms;
}

.animation-delay-900 {
  animation-delay: 900ms;
}

.animation-delay-1000 {
  animation-delay: 1000ms;
}

/* Glass morphism effect */
.glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Hover effects */
.group:hover .group-hover\:opacity-20 {
  opacity: 0.2;
}
</style>