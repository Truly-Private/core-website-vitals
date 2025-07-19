<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push({ name: 'home' })
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="text-center">
        <!-- 404 Illustration -->
        <div class="flex justify-center mb-8">
          <div class="relative">
            <div class="text-9xl font-bold text-primary-600 opacity-20">
              404
            </div>
            <div class="absolute inset-0 flex items-center justify-center">
              <i class="lucide-search-x w-16 h-16 text-primary-600"></i>
            </div>
          </div>
        </div>
        
        <h1 class="text-3xl font-bold text-gray-900 mb-4">
          {{ $t('errors.not_found_title') || 'Page Not Found' }}
        </h1>
        
        <p class="text-lg text-gray-600 mb-8">
          {{ $t('errors.not_found_message') || 'The page you are looking for does not exist.' }}
        </p>
        
        <div class="space-y-4">
          <button
            @click="goHome"
            class="btn btn-primary w-full sm:w-auto"
          >
            <i class="lucide-home w-4 h-4 mr-2"></i>
            {{ $t('common.go_home') || 'Go Home' }}
          </button>
          
          <button
            @click="goBack"
            class="btn btn-outline w-full sm:w-auto sm:ml-4"
          >
            <i class="lucide-arrow-left w-4 h-4 mr-2"></i>
            {{ $t('common.go_back') || 'Go Back' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Helpful Links -->
    <div class="mt-16 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <h2 class="text-lg font-medium text-gray-900 mb-4">
          {{ $t('common.helpful_links') || 'Helpful Links' }}
        </h2>
        
        <nav class="space-y-2">
          <router-link
            to="/"
            class="flex items-center text-sm text-gray-600 hover:text-primary-600"
          >
            <i class="lucide-home w-4 h-4 mr-2"></i>
            {{ $t('navigation.home') }}
          </router-link>
          
          <router-link
            to="/dashboard"
            class="flex items-center text-sm text-gray-600 hover:text-primary-600"
          >
            <i class="lucide-layout-dashboard w-4 h-4 mr-2"></i>
            {{ $t('navigation.dashboard') }}
          </router-link>
          
          <router-link
            to="/analysis"
            class="flex items-center text-sm text-gray-600 hover:text-primary-600"
          >
            <i class="lucide-search w-4 h-4 mr-2"></i>
            {{ $t('navigation.analysis') }}
          </router-link>
          
          <router-link
            to="/history"
            class="flex items-center text-sm text-gray-600 hover:text-primary-600"
          >
            <i class="lucide-history w-4 h-4 mr-2"></i>
            {{ $t('navigation.history') }}
          </router-link>
          
          <router-link
            to="/profile"
            class="flex items-center text-sm text-gray-600 hover:text-primary-600"
          >
            <i class="lucide-user w-4 h-4 mr-2"></i>
            {{ $t('navigation.profile') }}
          </router-link>
        </nav>
      </div>
    </div>
    
    <!-- Contact Support -->
    <div class="mt-8 text-center">
      <p class="text-sm text-gray-500">
        {{ $t('common.need_help') || 'Need help?' }}
        <a
          href="mailto:support@corewebsitevitals.com"
          class="text-primary-600 hover:text-primary-500 ml-1"
        >
          {{ $t('common.contact_support') || 'Contact Support' }}
        </a>
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Custom animation for the 404 number */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

.text-9xl {
  animation: float 3s ease-in-out infinite;
}

/* Hover effect for navigation links */
nav a {
  transition: all 0.2s ease-in-out;
}

nav a:hover {
  transform: translateX(4px);
}
</style>