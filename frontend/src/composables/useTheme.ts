import { ref, watchEffect, computed } from 'vue'

type Theme = 'light' | 'dark' | 'system'

const THEME_KEY = 'cwv-theme-preference'

// Reactive theme state
const currentTheme = ref<Theme>('system')
const resolvedTheme = ref<'light' | 'dark'>('dark')

// Initialize theme from localStorage or system preference
function initializeTheme() {
  const savedTheme = localStorage.getItem(THEME_KEY) as Theme | null
  if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
    currentTheme.value = savedTheme
  }
  
  applyTheme()
}

// Get system color scheme preference
function getSystemTheme(): 'light' | 'dark' {
  // Default to dark mode if no system preference is available
  if (!window.matchMedia) {
    return 'dark'
  }
  
  // Check system preference
  if (window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  
  // Default to dark mode
  return 'dark'
}

// Apply theme to DOM
function applyTheme() {
  let theme: 'light' | 'dark'
  
  if (currentTheme.value === 'system') {
    theme = getSystemTheme()
  } else {
    theme = currentTheme.value
  }
  
  resolvedTheme.value = theme
  
  // Update DOM
  document.documentElement.setAttribute('data-theme', theme)
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]')
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', theme === 'dark' ? '#202124' : '#ffffff')
  }
}

// Watch for system theme changes
if (window.matchMedia) {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', () => {
    if (currentTheme.value === 'system') {
      applyTheme()
    }
  })
}

export function useTheme() {
  // Initialize on first use
  if (typeof window !== 'undefined' && !document.documentElement.hasAttribute('data-theme')) {
    initializeTheme()
  }
  
  // Set theme function
  const setTheme = (theme: Theme) => {
    currentTheme.value = theme
    localStorage.setItem(THEME_KEY, theme)
    applyTheme()
  }
  
  // Toggle between light and dark
  const toggleTheme = () => {
    const newTheme = resolvedTheme.value === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }
  
  // Computed properties
  const isDark = computed(() => resolvedTheme.value === 'dark')
  const isLight = computed(() => resolvedTheme.value === 'light')
  const isSystem = computed(() => currentTheme.value === 'system')
  
  // Watch for theme changes
  watchEffect(() => {
    applyTheme()
  })
  
  return {
    currentTheme: computed(() => currentTheme.value),
    resolvedTheme: computed(() => resolvedTheme.value),
    isDark,
    isLight,
    isSystem,
    setTheme,
    toggleTheme,
  }
}