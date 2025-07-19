<template>
  <div class="billing-view">
    <div class="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
        <p class="mt-2 text-gray-600">Manage your subscription and billing information</p>
      </div>

      <!-- Current Subscription -->
      <div class="bg-white shadow rounded-lg p-6 mb-8">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Current Subscription</h2>
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center">
              <span class="text-2xl font-bold text-gray-900 capitalize">{{ currentPlan.name }}</span>
              <span 
                :class="[
                  'ml-3 px-2 py-1 text-xs font-medium rounded-full',
                  currentPlan.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                ]"
              >
                {{ currentPlan.status }}
              </span>
            </div>
            <p class="text-gray-500 mt-1">
              <span class="font-medium">${{ currentPlan.price }}</span>/month
            </p>
            <p class="text-sm text-gray-500 mt-1">
              {{ currentPlan.description }}
            </p>
            <p v-if="currentPlan.nextBillingDate" class="text-sm text-gray-500 mt-2">
              Next billing: {{ formatDate(currentPlan.nextBillingDate) }}
            </p>
          </div>
          <div class="flex space-x-3">
            <button
              v-if="currentPlan.name !== 'free'"
              @click="cancelSubscription"
              class="px-4 py-2 text-red-600 border border-red-600 rounded-md hover:bg-red-50"
            >
              Cancel
            </button>
            <button
              @click="showPlans = true"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {{ currentPlan.name === 'free' ? 'Upgrade' : 'Change Plan' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Usage Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-2">Analyses This Month</h3>
          <div class="flex items-center">
            <span class="text-3xl font-bold text-blue-600">{{ usage.analyses }}</span>
            <span class="text-gray-500 ml-1">/ {{ limits.analyses === -1 ? '∞' : limits.analyses }}</span>
          </div>
          <div class="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${Math.min((usage.analyses / limits.analyses) * 100, 100)}%` }"
            ></div>
          </div>
        </div>

        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-2">Team Members</h3>
          <div class="flex items-center">
            <span class="text-3xl font-bold text-green-600">{{ usage.teamMembers }}</span>
            <span class="text-gray-500 ml-1">/ {{ limits.teamMembers === -1 ? '∞' : limits.teamMembers }}</span>
          </div>
          <div class="mt-2 bg-gray-200 rounded-full h-2">
            <div 
              class="bg-green-600 h-2 rounded-full transition-all duration-300"
              :style="{ width: `${Math.min((usage.teamMembers / limits.teamMembers) * 100, 100)}%` }"
            ></div>
          </div>
        </div>

        <div class="bg-white shadow rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-2">Data Retention</h3>
          <div class="flex items-center">
            <span class="text-3xl font-bold text-purple-600">{{ limits.dataRetention }}</span>
            <span class="text-gray-500 ml-1">days</span>
          </div>
        </div>
      </div>

      <!-- Billing History -->
      <div class="bg-white shadow rounded-lg p-6 mb-8">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Billing History</h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Invoice
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="invoice in billingHistory" :key="invoice.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ formatDate(invoice.date) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ invoice.description }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  ${{ invoice.amount }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="[
                    'px-2 py-1 text-xs font-medium rounded-full',
                    invoice.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  ]">
                    {{ invoice.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                  <a :href="invoice.invoiceUrl" target="_blank" class="hover:underline">
                    Download
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Payment Method -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-4">Payment Method</h2>
        <div v-if="paymentMethod" class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="w-8 h-8 bg-gray-200 rounded flex items-center justify-center">
              <span class="text-xs font-medium">{{ paymentMethod.brand.toUpperCase() }}</span>
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-gray-900">
                •••• •••• •••• {{ paymentMethod.last4 }}
              </p>
              <p class="text-sm text-gray-500">
                Expires {{ paymentMethod.expMonth }}/{{ paymentMethod.expYear }}
              </p>
            </div>
          </div>
          <button
            @click="updatePaymentMethod"
            class="px-4 py-2 text-blue-600 border border-blue-600 rounded-md hover:bg-blue-50"
          >
            Update
          </button>
        </div>
        <div v-else class="text-center py-8">
          <p class="text-gray-500 mb-4">No payment method on file</p>
          <button
            @click="addPaymentMethod"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Payment Method
          </button>
        </div>
      </div>
    </div>

    <!-- Subscription Plans Modal -->
    <div v-if="showPlans" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-lg font-medium text-gray-900">Choose Your Plan</h3>
            <button
              @click="showPlans = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div v-for="plan in plans" :key="plan.id" class="border rounded-lg p-6 relative">
              <div v-if="plan.name === 'pro'" class="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 text-xs rounded-bl-lg">
                Popular
              </div>
              <h4 class="text-xl font-bold text-gray-900 capitalize">{{ plan.name }}</h4>
              <p class="text-gray-600 mt-2">{{ plan.description }}</p>
              <div class="mt-4">
                <span class="text-4xl font-bold text-gray-900">${{ plan.price }}</span>
                <span class="text-gray-500">/month</span>
              </div>
              <ul class="mt-6 space-y-3">
                <li v-for="feature in plan.features" :key="feature" class="flex items-center">
                  <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  {{ feature }}
                </li>
              </ul>
              <button
                @click="selectPlan(plan)"
                :disabled="currentPlan.name === plan.name"
                :class="[
                  'w-full mt-6 px-4 py-2 rounded-md font-medium',
                  currentPlan.name === plan.name
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                ]"
              >
                {{ currentPlan.name === plan.name ? 'Current Plan' : 'Select Plan' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const showPlans = ref(false)

const currentPlan = reactive({
  name: 'free',
  price: 0,
  status: 'active',
  description: 'Basic SEO analysis with limited features',
  nextBillingDate: null
})

const usage = reactive({
  analyses: 12,
  teamMembers: 1
})

const limits = reactive({
  analyses: 50,
  teamMembers: 1,
  dataRetention: 30
})

const billingHistory = ref([
  {
    id: 1,
    date: '2024-01-15',
    description: 'Monthly subscription - Pro Plan',
    amount: 29.99,
    status: 'paid',
    invoiceUrl: '#'
  },
  {
    id: 2,
    date: '2023-12-15',
    description: 'Monthly subscription - Pro Plan',
    amount: 29.99,
    status: 'paid',
    invoiceUrl: '#'
  }
])

const paymentMethod = ref({
  brand: 'visa',
  last4: '4242',
  expMonth: '12',
  expYear: '2025'
})

const plans = ref([
  {
    id: 'free',
    name: 'free',
    price: 0,
    description: 'Perfect for getting started',
    features: [
      '10 analyses per month',
      'Basic SEO reports',
      'Email support',
      '30-day data retention'
    ]
  },
  {
    id: 'pro',
    name: 'pro',
    price: 29.99,
    description: 'Best for growing businesses',
    features: [
      '100 analyses per month',
      'Advanced SEO reports',
      'Priority support',
      'Team collaboration',
      '1-year data retention',
      'Custom branding'
    ]
  },
  {
    id: 'enterprise',
    name: 'enterprise',
    price: 99.99,
    description: 'For large organizations',
    features: [
      'Unlimited analyses',
      'White-label reports',
      'Dedicated support',
      'Unlimited team members',
      'Custom integrations',
      'Advanced analytics'
    ]
  }
])

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const selectPlan = async (plan: any) => {
  if (plan.name === currentPlan.name) return
  
  try {
    // This would integrate with a payment processor like Stripe
    console.log('Selecting plan:', plan.name)
    
    // For now, just simulate the plan change
    currentPlan.name = plan.name
    currentPlan.price = plan.price
    currentPlan.description = plan.description
    
    if (plan.name !== 'free') {
      currentPlan.nextBillingDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
    }
    
    showPlans.value = false
    alert(`Successfully switched to ${plan.name} plan!`)
  } catch (error) {
    console.error('Plan selection error:', error)
    alert('Failed to change plan. Please try again.')
  }
}

const cancelSubscription = async () => {
  if (confirm('Are you sure you want to cancel your subscription?')) {
    try {
      // This would call the API to cancel the subscription
      console.log('Canceling subscription')
      
      // For now, just simulate the cancellation
      currentPlan.name = 'free'
      currentPlan.price = 0
      currentPlan.status = 'cancelled'
      currentPlan.nextBillingDate = null
      
      alert('Subscription cancelled successfully')
    } catch (error) {
      console.error('Cancellation error:', error)
      alert('Failed to cancel subscription. Please contact support.')
    }
  }
}

const addPaymentMethod = () => {
  // This would open a payment method form or redirect to payment processor
  console.log('Adding payment method')
  alert('Payment method form would open here')
}

const updatePaymentMethod = () => {
  // This would open a payment method update form
  console.log('Updating payment method')
  alert('Payment method update form would open here')
}
</script>

<style scoped>
.billing-view {
  min-height: 100vh;
  background-color: #f9fafb;
}
</style>