<template>
  <div
    class="feature-card group relative overflow-hidden rounded-xl p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl"
    :class="[
      variant === 'glass' ? 'glass-card' : 'solid-card',
      `delay-${delay}`
    ]"
  >
    <!-- Background gradient on hover -->
    <div class="absolute inset-0 bg-gradient-to-br from-var(--color-primary) to-var(--color-primary-dark) opacity-0 group-hover:opacity-10 transition-opacity duration-300"></div>
    
    <!-- Icon -->
    <div class="relative z-10 mb-4">
      <div
        class="inline-flex items-center justify-center w-12 h-12 rounded-lg transition-all duration-300"
        :class="[
          variant === 'glass' 
            ? 'bg-white/20 text-var(--color-primary) group-hover:bg-var(--color-primary) group-hover:text-white' 
            : 'bg-var(--color-primary)/10 text-var(--color-primary) group-hover:bg-var(--color-primary) group-hover:text-white'
        ]"
      >
        <component :is="icon" class="w-6 h-6" />
      </div>
    </div>
    
    <!-- Content -->
    <div class="relative z-10">
      <h3 class="text-lg font-semibold mb-2 transition-colors duration-300"
          :class="[
            variant === 'glass' ? 'text-white' : 'text-var(--color-text-primary)'
          ]">
        {{ title }}
      </h3>
      <p class="text-sm leading-relaxed transition-colors duration-300"
         :class="[
           variant === 'glass' ? 'text-white/80' : 'text-var(--color-text-secondary)'
         ]">
        {{ description }}
      </p>
      
      <!-- Optional CTA -->
      <div v-if="showCta" class="mt-4">
        <button
          class="inline-flex items-center text-sm font-medium transition-all duration-300"
          :class="[
            variant === 'glass' 
              ? 'text-white hover:text-white/80' 
              : 'text-var(--color-primary) hover:text-var(--color-primary-dark)'
          ]"
        >
          {{ ctaText }}
          <ArrowRightIcon class="w-4 h-4 ml-1 transform group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
    
    <!-- Decorative elements -->
    <div v-if="showDecoration" class="absolute -bottom-6 -right-6 w-24 h-24 rounded-full bg-gradient-to-br from-var(--color-primary)/20 to-var(--color-primary-light)/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
  </div>
</template>

<script setup lang="ts">
import { type Component } from 'vue'
import ArrowRightIcon from '@/components/icons/ArrowRightIcon.vue'

interface Props {
  icon: Component
  title: string
  description: string
  variant?: 'glass' | 'solid'
  delay?: number
  showCta?: boolean
  ctaText?: string
  showDecoration?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'solid',
  delay: 0,
  showCta: false,
  ctaText: 'Learn more',
  showDecoration: true
})
</script>

<style scoped>
/* Glass card styles */
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

[data-theme="dark"] .glass-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Solid card styles */
.solid-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

/* Animation delays */
.delay-0 {
  animation-delay: 0ms;
}

.delay-100 {
  animation-delay: 100ms;
}

.delay-200 {
  animation-delay: 200ms;
}

.delay-300 {
  animation-delay: 300ms;
}

.delay-400 {
  animation-delay: 400ms;
}

.delay-500 {
  animation-delay: 500ms;
}

/* Feature card animation */
.feature-card {
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Hover lift effect */
.feature-card:hover {
  transform: translateY(-4px) scale(1.02);
}

/* Focus styles for accessibility */
.feature-card:focus-within {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>