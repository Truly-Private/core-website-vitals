<template>
  <div class="app-layout">
    <!-- Header -->
    <header class="app-header">
      <div class="header-container">
        <div class="header-left">
          <router-link to="/" class="logo-link">
            <div class="logo">
              <svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="logo-text">Core Website Vitals</span>
            </div>
          </router-link>
        </div>
        
        <nav class="header-nav">
          <router-link 
            v-for="item in navItems" 
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: isActiveRoute(item.path) }"
          >
            <component :is="item.icon" class="nav-icon" />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
        
        <div class="header-right">
          <ThemeToggle />
          
          <div class="user-menu">
            <button @click="toggleUserMenu" class="user-menu-button">
              <div class="user-avatar">
                {{ userInitials }}
              </div>
              <ChevronDownIcon class="chevron-icon" />
            </button>
            
            <Transition name="dropdown">
              <div v-if="isUserMenuOpen" class="user-dropdown">
                <router-link to="/profile" class="dropdown-item">
                  <UserIcon class="dropdown-icon" />
                  <span>Profile</span>
                </router-link>
                <router-link to="/settings" class="dropdown-item">
                  <SettingsIcon class="dropdown-icon" />
                  <span>Settings</span>
                </router-link>
                <router-link to="/billing" class="dropdown-item">
                  <CreditCardIcon class="dropdown-icon" />
                  <span>Billing</span>
                </router-link>
                <hr class="dropdown-divider" />
                <button @click="handleLogout" class="dropdown-item logout">
                  <LogOutIcon class="dropdown-icon" />
                  <span>Logout</span>
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="app-main">
      <div class="main-container">
        <slot />
      </div>
    </main>
    
    <!-- Footer -->
    <footer class="app-footer">
      <div class="footer-container">
        <p>&copy; 2024 Core Website Vitals. All rights reserved.</p>
        <div class="footer-links">
          <a href="/privacy" class="footer-link">Privacy</a>
          <a href="/terms" class="footer-link">Terms</a>
          <a href="/contact" class="footer-link">Contact</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'
import { 
  HomeIcon, 
  BarChartIcon, 
  ClockIcon, 
  UserIcon, 
  SettingsIcon, 
  CreditCardIcon, 
  LogOutIcon,
  ChevronDownIcon 
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isUserMenuOpen = ref(false)

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: HomeIcon },
  { path: '/analysis', label: 'New Analysis', icon: BarChartIcon },
  { path: '/history', label: 'History', icon: ClockIcon },
]

const userInitials = computed(() => {
  const user = authStore.user
  if (!user) return 'U'
  
  const name = user.full_name || user.email
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

function isActiveRoute(path: string) {
  return route.path.startsWith(path)
}

function toggleUserMenu() {
  isUserMenuOpen.value = !isUserMenuOpen.value
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.user-menu')) {
    isUserMenuOpen.value = false
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push({ name: 'home' })
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-background);
  color: var(--color-text-primary);
}

/* Header Styles */
.app-header {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.header-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-link {
  text-decoration: none;
  color: inherit;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: var(--color-primary);
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-nav {
  display: flex;
  gap: var(--spacing-xs);
  margin-left: var(--spacing-2xl);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background-color: var(--color-surface-variant);
  color: var(--color-text-primary);
}

.nav-link.active {
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
}

.nav-icon {
  width: 18px;
  height: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* User Menu */
.user-menu {
  position: relative;
}

.user-menu-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.user-menu-button:hover {
  background-color: var(--color-surface-variant);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  color: var(--color-text-secondary);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-sm);
  z-index: var(--z-dropdown);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  text-decoration: none;
  font-size: 0.875rem;
  transition: background-color var(--transition-fast);
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
}

.dropdown-item:hover {
  background-color: var(--color-surface-variant);
}

.dropdown-item.logout {
  color: var(--color-danger);
}

.dropdown-icon {
  width: 18px;
  height: 18px;
}

.dropdown-divider {
  margin: var(--spacing-xs) 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

/* Main Content */
.app-main {
  flex: 1;
  padding: var(--spacing-xl) 0;
}

.main-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

/* Footer */
.app-footer {
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
  padding: var(--spacing-lg) 0;
  margin-top: auto;
}

.footer-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.footer-links {
  display: flex;
  gap: var(--spacing-lg);
}

.footer-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-link:hover {
  color: var(--color-text-primary);
}

/* Transitions */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive */
@media (max-width: 768px) {
  .header-nav {
    display: none;
  }
  
  .footer-container {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }
}
</style>