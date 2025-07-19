<template>
  <div class="group relative">
    <div class="flex items-center justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-2">
          <h4 class="text-sm font-medium text-white/90">{{ metric.label }}</h4>
          <button
            class="text-white/50 hover:text-white/80 transition-colors"
            @mouseenter="showTooltip = true"
            @mouseleave="showTooltip = false"
          >
            <InfoIcon class="w-4 h-4" />
          </button>
        </div>
        <div class="flex items-baseline space-x-1 mt-1">
          <span class="text-2xl font-bold text-white">{{ formattedValue }}</span>
          <span class="text-sm text-white/70">{{ metric.unit }}</span>
        </div>
      </div>
      
      <div class="flex items-center space-x-3">
        <!-- Status indicator -->
        <div class="flex items-center space-x-2">
          <div
            class="w-3 h-3 rounded-full"
            :class="{
              'bg-green-400': metric.status === 'good',
              'bg-yellow-400': metric.status === 'needs-improvement',
              'bg-red-400': metric.status === 'poor'
            }"
          ></div>
          <span class="text-xs text-white/70 capitalize">{{ metric.status }}</span>
        </div>
      </div>
    </div>
    
    <!-- Progress bar -->
    <div class="mt-3 relative">
      <div class="h-2 bg-white/20 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500 ease-out"
          :class="{
            'bg-green-400': metric.status === 'good',
            'bg-yellow-400': metric.status === 'needs-improvement',
            'bg-red-400': metric.status === 'poor'
          }"
          :style="`width: ${progressWidth}%`"
        ></div>
      </div>
      <div
        class="absolute top-0 h-2 w-0.5 bg-white/60"
        :style="`left: ${thresholdPosition}%`"
      ></div>
    </div>
    
    <!-- Tooltip -->
    <Transition name="tooltip">
      <div
        v-if="showTooltip"
        class="absolute bottom-full left-0 mb-2 w-64 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl z-10"
      >
        <p class="font-medium mb-1">{{ metric.name }} - {{ metric.label }}</p>
        <p class="text-xs text-gray-300 mb-2">{{ getMetricDescription(metric.name) }}</p>
        <p class="text-xs">
          <span class="text-gray-400">Good threshold:</span>
          <span class="text-green-400 ml-1">&lt; {{ metric.threshold }}{{ metric.unit }}</span>
        </p>
        <div class="absolute top-full left-4 w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-gray-900"></div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import InfoIcon from '@/components/icons/InfoIcon.vue'

interface Metric {
  name: string
  label: string
  value: number
  unit: string
  status: 'good' | 'needs-improvement' | 'poor'
  threshold: number
  delay: number
}

const props = defineProps<{
  metric: Metric
}>()

const showTooltip = ref(false)

const formattedValue = computed(() => {
  if (props.metric.name === 'CLS') {
    return props.metric.value.toFixed(3)
  }
  return props.metric.value.toFixed(1)
})

const progressWidth = computed(() => {
  const maxValue = props.metric.threshold * 2
  return Math.min((props.metric.value / maxValue) * 100, 100)
})

const thresholdPosition = computed(() => {
  const maxValue = props.metric.threshold * 2
  return (props.metric.threshold / maxValue) * 100
})

function getMetricDescription(name: string): string {
  const descriptions = {
    LCP: 'Measures loading performance. To provide a good user experience, LCP should occur within 2.5 seconds of when the page first starts loading.',
    FID: 'Measures interactivity. To provide a good user experience, pages should have a FID of 100 milliseconds or less.',
    CLS: 'Measures visual stability. To provide a good user experience, pages should maintain a CLS of 0.1 or less.'
  }
  return descriptions[name as keyof typeof descriptions] || ''
}
</script>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>