---
inclusion: always
---

# Code Patterns and Conventions

## Backend Patterns

### FastAPI Endpoint Pattern
```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth_service import get_current_user
from app.services.supabase_service import SupabaseService
from app.models.schemas import AnalysisTaskCreate, AnalysisTaskResponse

router = APIRouter()

@router.post("/", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    analysis_data: AnalysisTaskCreate,
    current_user: dict = Depends(get_current_user),
    db_service: SupabaseService = Depends(get_supabase_service)
):
    """Submit URL for SEO analysis."""
    # 1. Validate input
    # 2. Create database record
    # 3. Dispatch Celery task
    # 4. Return immediate response
```

### Celery Task Pattern
```python
from app.worker.celery_app import celery_app
from app.services.supabase_service import SupabaseService
from app.core.supabase import supabase_admin

@celery_app.task(bind=True, name='tasks.perform_seo_analysis')
def perform_seo_analysis(self, analysis_task_id: str, url: str):
    """Background task for SEO analysis."""
    db_service = SupabaseService(supabase_admin)
    
    try:
        # Update status to IN_PROGRESS
        db_service.update_analysis_task(task_id, {'status': 'IN_PROGRESS'})
        
        # Perform analysis
        results = analyze_url(url)
        
        # Store results
        db_service.update_analysis_task(task_id, {
            'status': 'SUCCESS',
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        # Handle errors gracefully
        db_service.update_analysis_task(task_id, {
            'status': 'FAILED',
            'error_message': str(e)
        })
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

### Supabase Service Pattern
```python
from supabase import Client
from typing import Dict, List, Optional

class SupabaseService:
    def __init__(self, client: Client):
        self.client = client
    
    def create_analysis_task(self, user_id: str, task_data: dict) -> Dict:
        """Create new analysis task with RLS protection."""
        response = self.client.table('analysis_tasks').insert({
            'user_id': user_id,
            **task_data
        }).execute()
        
        if response.data:
            return response.data[0]
        raise Exception("Failed to create analysis task")
    
    def get_user_analyses(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's analyses with automatic RLS filtering."""
        response = self.client.table('analysis_tasks')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('submitted_at', desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data or []
```

## Frontend Patterns

### Pinia Store Pattern
```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { analysisService } from '@/services/api'
import { supabase } from '@/services/supabase'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const analyses = ref<AnalysisTask[]>([])
  const isLoading = ref(false)
  
  // Getters
  const recentAnalyses = computed(() => 
    analyses.value.slice(0, 10)
  )
  
  // Actions
  async function submitAnalysis(url: string) {
    isLoading.value = true
    try {
      const task = await analysisService.submitAnalysis({ url })
      analyses.value.unshift(task)
      return task
    } finally {
      isLoading.value = false
    }
  }
  
  // Real-time subscriptions
  function subscribeToUpdates(userId: string) {
    return supabase
      .channel('analysis_tasks')
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'analysis_tasks',
        filter: `user_id=eq.${userId}`
      }, handleRealtimeUpdate)
      .subscribe()
  }
  
  return { analyses, isLoading, recentAnalyses, submitAnalysis, subscribeToUpdates }
})
```

### Vue Component Pattern
```vue
<template>
  <div class="analysis-form">
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="url" class="block text-sm font-medium">Website URL</label>
        <input
          id="url"
          v-model="formData.url"
          type="url"
          required
          class="mt-1 block w-full rounded-md border-gray-300"
          placeholder="https://example.com"
        />
      </div>
      
      <button
        type="submit"
        :disabled="isSubmitting"
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
      >
        {{ isSubmitting ? 'Analyzing...' : 'Analyze Website' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAnalysisStore } from '@/stores/analysis'
import { useNotifications } from '@/composables/useNotifications'

const analysisStore = useAnalysisStore()
const { showNotification } = useNotifications()

const isSubmitting = ref(false)
const formData = reactive({
  url: ''
})

async function handleSubmit() {
  isSubmitting.value = true
  
  try {
    await analysisStore.submitAnalysis(formData.url)
    showNotification('Analysis started! You will be notified when complete.', 'success')
    formData.url = ''
  } catch (error) {
    showNotification('Failed to start analysis. Please try again.', 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>
```