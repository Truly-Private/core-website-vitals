<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'
import HeroSection from '@/components/home/HeroSection.vue'
import FeatureCard from '@/components/ui/FeatureCard.vue'
import SearchIcon from '@/components/icons/SearchIcon.vue'
import ZapIcon from '@/components/icons/ZapIcon.vue'
import TrendingUpIcon from '@/components/icons/TrendingUpIcon.vue'
import FileTextIcon from '@/components/icons/FileTextIcon.vue'
import UsersIcon from '@/components/icons/UsersIcon.vue'
import ShieldIcon from '@/components/icons/ShieldIcon.vue'

const authStore = useAuthStore()
const router = useRouter()

onMounted(() => {
  // Redirect to dashboard if user is already authenticated
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  }
})

const handleGetStarted = () => {
  if (authStore.isAuthenticated) {
    router.push({ name: 'dashboard' })
  } else {
    router.push({ name: 'trial' })
  }
}

const handleLogin = () => {
  router.push({ name: 'login' })
}

const handleTryFree = () => {
  router.push({ name: 'trial' })
}

const features = [
  {
    icon: SearchIcon,
    title: 'Comprehensive SEO Analysis',
    description: 'Get detailed insights into your website\'s SEO performance with our advanced analysis tools.',
  },
  {
    icon: ZapIcon,
    title: 'Performance Monitoring',
    description: 'Track your Core Web Vitals and page performance metrics to improve user experience.',
  },
  {
    icon: TrendingUpIcon,
    title: 'Trend Analysis',
    description: 'Monitor your SEO progress over time with detailed trend analysis and historical data.',
  },
  {
    icon: FileTextIcon,
    title: 'Detailed Reports',
    description: 'Generate comprehensive reports with actionable recommendations for improvement.',
  },
  {
    icon: UsersIcon,
    title: 'Team Collaboration',
    description: 'Work together with your team to improve your website\'s SEO performance.',
  },
  {
    icon: ShieldIcon,
    title: 'Secure & Reliable',
    description: 'Your data is secure with enterprise-grade security and 99.9% uptime guarantee.',
  },
]

const testimonials = [
  {
    name: 'Sarah Johnson',
    role: 'Digital Marketing Manager',
    company: 'TechCorp',
    avatar: '/sarah.svg',
    content: 'Core Website Vitals has transformed how we approach SEO. The insights are incredible and the reports are exactly what we need.',
  },
  {
    name: 'Michael Chen',
    role: 'SEO Specialist',
    company: 'GrowthAgency',
    avatar: '/michael.svg',
    content: 'The most comprehensive SEO analysis tool I\'ve ever used. The real-time monitoring and detailed recommendations are game-changers.',
  },
  {
    name: 'Emma Davis',
    role: 'Web Developer',
    company: 'StartupXYZ',
    avatar: '/emma.svg',
    content: 'As a developer, I love how technical and detailed the analysis is. It helps me optimize our website\'s performance effectively.',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- Header -->
    <header class="home-header">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <h1 class="text-2xl font-bold text-primary-600">
                Core Website Vitals
              </h1>
            </div>
          </div>
          
          <div class="flex items-center space-x-4">
            <ThemeToggle />
            <button
              @click="handleLogin"
              class="text-gray-700 hover:text-primary-600 px-3 py-2 text-sm font-medium"
            >
              {{ $t('auth.login.title') }}
            </button>
            <button
              @click="handleGetStarted"
              class="btn btn-primary"
            >
              {{ $t('common.get_started') }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <HeroSection 
      @try-free="handleTryFree"
      @login="handleLogin"
    />

    <!-- Features Section -->
    <section class="features-section">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="section-title">
            Powerful Features for SEO Success
          </h2>
          <p class="section-subtitle">
            Everything you need to analyze, monitor, and improve your website's SEO performance
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard
            v-for="(feature, index) in features"
            :key="feature.title"
            :icon="feature.icon"
            :title="feature.title"
            :description="feature.description"
            :delay="index * 100"
            variant="solid"
          />
        </div>
      </div>
    </section>

    <!-- Testimonials Section -->
    <section class="testimonials-section">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="section-title">
            Trusted by SEO Professionals
          </h2>
          <p class="section-subtitle">
            See what our customers are saying about Core Website Vitals
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="testimonial in testimonials"
            :key="testimonial.name"
            class="testimonial-card"
          >
            <div class="flex items-center mb-4">
              <img
                :src="testimonial.avatar"
                :alt="testimonial.name"
                class="w-12 h-12 rounded-full mr-4"
                @error="$event.target.src = '/avatars/default.svg'"
              >
              <div>
                <h4 class="testimonial-name">{{ testimonial.name }}</h4>
                <p class="testimonial-role">{{ testimonial.role }}, {{ testimonial.company }}</p>
              </div>
            </div>
            <p class="testimonial-content">
              "{{ testimonial.content }}"
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="cta-title">
          Ready to Optimize Your Website?
        </h2>
        <p class="cta-subtitle">
          Join thousands of professionals who trust Core Website Vitals for their SEO analysis needs.
        </p>
        <button
          @click="handleGetStarted"
          class="btn btn-secondary btn-lg"
        >
          {{ $t('common.get_started') }}
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="site-footer">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 class="text-lg font-semibold mb-4">Core Website Vitals</h3>
            <p class="footer-description">
              The most comprehensive SEO analysis platform for digital professionals.
            </p>
          </div>
          
          <div>
            <h4 class="footer-heading">Product</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#" class="footer-link">Features</a></li>
              <li><a href="#" class="footer-link">Pricing</a></li>
              <li><a href="#" class="footer-link">API</a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="footer-heading">Company</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#" class="footer-link">About</a></li>
              <li><a href="#" class="footer-link">Blog</a></li>
              <li><a href="#" class="footer-link">Careers</a></li>
            </ul>
          </div>
          
          <div>
            <h4 class="footer-heading">Support</h4>
            <ul class="space-y-2 text-sm">
              <li><a href="#" class="footer-link">Help Center</a></li>
              <li><a href="#" class="footer-link">Contact</a></li>
              <li><a href="#" class="footer-link">Status</a></li>
            </ul>
          </div>
        </div>
        
        <div class="footer-bottom">
          <p>{{ $t('footer.copyright') }}</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Home page base */
.home-page {
  min-height: 100vh;
  background-color: var(--color-background);
  transition: background-color var(--transition-base), color var(--transition-base);
}

/* Header styles with theme support */
.home-header {
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  transition: background-color var(--transition-base), border-color var(--transition-base);
}

/* Section styles */
.features-section {
  padding: 5rem 0;
  background-color: var(--color-surface);
  transition: background-color var(--transition-base);
}

[data-theme="light"] .features-section {
  background-color: var(--color-surface-variant);
}

.testimonials-section {
  padding: 5rem 0;
  background-color: var(--color-surface-variant);
  transition: background-color var(--transition-base);
}

[data-theme="light"] .testimonials-section {
  background-color: var(--color-surface);
}

.cta-section {
  padding: 5rem 0;
  background-color: var(--color-primary);
  color: var(--color-text-on-primary);
}

.cta-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-on-primary);
  margin-bottom: 1rem;
}

@media (min-width: 768px) {
  .cta-title {
    font-size: 2.25rem;
  }
}

.cta-subtitle {
  font-size: 1.25rem;
  opacity: 0.9;
  max-width: 42rem;
  margin: 0 auto 2rem;
}

/* Section typography */
.section-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1rem;
}

@media (min-width: 768px) {
  .section-title {
    font-size: 2.25rem;
  }
}

.section-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  max-width: 48rem;
  margin: 0 auto;
}

/* Testimonial cards */
.testimonial-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  transition: all var(--transition-base);
}

.testimonial-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.testimonial-name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.testimonial-role {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.testimonial-content {
  color: var(--color-text-secondary);
  font-style: italic;
}

/* Footer styles */
.site-footer {
  background-color: var(--color-surface-variant);
  color: var(--color-text-primary);
  border-top: 1px solid var(--color-border);
}

[data-theme="dark"] .site-footer {
  background-color: rgb(17 24 39);
  color: rgb(255 255 255);
}

.footer-heading {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--color-text-primary);
}

[data-theme="dark"] .footer-heading {
  color: rgb(209 213 219);
}

.footer-description {
  color: var(--color-text-secondary);
}

[data-theme="dark"] .footer-description {
  color: rgb(156 163 175);
}

.footer-link {
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}

.footer-link:hover {
  color: var(--color-text-primary);
}

[data-theme="dark"] .footer-link {
  color: rgb(156 163 175);
}

[data-theme="dark"] .footer-link:hover {
  color: rgb(255 255 255);
}

.footer-bottom {
  border-top: 1px solid var(--color-border);
  margin-top: 2rem;
  padding-top: 2rem;
  text-align: center;
  color: var(--color-text-secondary);
}

[data-theme="dark"] .footer-bottom {
  border-top-color: rgb(55 65 81);
  color: rgb(156 163 175);
}

/* Button adjustments */
.text-gray-700 {
  color: var(--color-text-primary);
}

.hover\:text-primary-600:hover {
  color: var(--color-primary);
}

/* Animation for feature cards */
.hover\:shadow-md:hover {
  box-shadow: var(--shadow-md);
}
</style>