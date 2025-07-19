<template>
  <div class="theme-toggle">
    <button
      @click="toggleMenu"
      class="theme-toggle-button"
      :aria-label="`Current theme: ${currentTheme}`"
      aria-haspopup="true"
      :aria-expanded="isOpen"
    >
      <Transition name="fade" mode="out-in">
        <SunIcon v-if="resolvedTheme === 'light'" class="theme-icon" />
        <MoonIcon v-else class="theme-icon" />
      </Transition>
    </button>
    
    <Transition name="dropdown">
      <div v-if="isOpen" class="theme-menu" role="menu">
        <button
          v-for="option in themeOptions"
          :key="option.value"
          @click="selectTheme(option.value)"
          class="theme-option"
          :class="{ active: currentTheme === option.value }"
          role="menuitem"
        >
          <component :is="option.icon" class="option-icon" />
          <span>{{ option.label }}</span>
          <CheckIcon v-if="currentTheme === option.value" class="check-icon" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTheme } from '@/composables/useTheme'
import SunIcon from '@/components/icons/SunIcon.vue'
import MoonIcon from '@/components/icons/MoonIcon.vue'
import SystemIcon from '@/components/icons/SystemIcon.vue'
import CheckIcon from '@/components/icons/CheckIcon.vue'

const { currentTheme, resolvedTheme, setTheme } = useTheme()
const isOpen = ref(false)

const themeOptions = [
  { value: 'light' as const, label: 'Light', icon: SunIcon },
  { value: 'dark' as const, label: 'Dark', icon: MoonIcon },
  { value: 'system' as const, label: 'System', icon: SystemIcon },
]

function toggleMenu() {
  isOpen.value = !isOpen.value
}

function selectTheme(theme: 'light' | 'dark' | 'system') {
  setTheme(theme)
  isOpen.value = false
}

// Close menu on outside click
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.theme-toggle')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.theme-toggle {
  position: relative;
}

.theme-toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.theme-toggle-button:hover {
  background-color: var(--color-surface-variant);
}

.theme-toggle-button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.theme-icon {
  width: 20px;
  height: 20px;
  color: var(--color-text-primary);
}

.theme-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  padding: var(--spacing-sm);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
}

.theme-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-primary);
  transition: background-color var(--transition-fast);
}

.theme-option:hover {
  background-color: var(--color-surface-variant);
}

.theme-option.active {
  color: var(--color-primary);
  font-weight: 500;
}

.option-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.check-icon {
  width: 16px;
  height: 16px;
  margin-left: auto;
  color: var(--color-primary);
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>