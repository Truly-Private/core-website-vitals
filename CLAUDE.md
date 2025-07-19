# CLAUDE.md - Core Website Vitals

> **Project**: Transform ihuzaifashoukat/seo-analyzer into a full-stack SaaS platform  
> **Domain**: corewebsitevitals.com  
> **Status**: Active Development  
> **Last Updated**: 2025-07-17

## Project Overview

Core Website Vitals is a comprehensive SaaS platform that transforms the command-line python-seo-analyzer tool into a user-friendly web application. The platform enables users to perform SEO analysis through an intuitive dashboard, track historical performance, and receive actionable insights.

### Key Transformation
- **From**: Command-line Python utility for technical users
- **To**: Multi-tenant web application serving digital marketers, developers, and SEO professionals
- **Value**: Democratizes advanced SEO analysis with superior UX and real-time features

## Architecture Overview

### Technology Stack

| Layer | Technology | Purpose | Key Features |
|-------|------------|---------|--------------|
| **Frontend** | Vue.js 3 + TypeScript + Vite | User Interface | Composition API, Pinia state management, real-time updates |
| **Backend API** | FastAPI + Python 3.11+ | REST API Server | Async-first, auto-generated docs, dependency injection |
| **Database** | Supabase (PostgreSQL) | Data Persistence | Managed database, RLS policies, real-time subscriptions |
| **Task Queue** | Celery + Redis | Background Processing | Async SEO analysis, retry logic, scaling |
| **Authentication** | Supabase Auth + JWT | User Management | Multi-factor auth, social logins, session management |
| **Knowledge Graph** | Neo4j | Context Memory | Graph database for storing AI assistant memories |
| **Deployment** | Docker + Docker Compose | Containerization | Consistent environments, easy scaling |

### System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Vue.js SPA    │───▶│     Nginx    │───▶│  FastAPI Server │
│   (Frontend)    │    │(Reverse Proxy)│    │   (Backend)     │
└─────────────────┘    └──────────────┘    └────────┬────────┘
         │                                           │
         │ WebSocket/HTTP                            │ SQL Queries
         ▼                                           ▼
┌─────────────────┐                        ┌─────────────────┐
│   Supabase DB   │                        │   Redis Cache   │
│(Users, Results) │                        │  (Task Queue)   │
└─────────────────┘                        └────────┬────────┘
         ▲                                           │
         │ Database Operations                       │ Task Messages
         │                                           ▼
         └─────────────────┐              ┌─────────────────┐
                           │              │  Celery Worker  │
                           └──────────────│ (SEO Analysis)  │
                                          └─────────────────┘
                                                   ▲
                                                   │ Memory Management
                                                   ▼
                                          ┌─────────────────┐
                                          │     Neo4j      │
                                          │ (Knowledge Graph)│
                                          └─────────────────┘
```

### AI Memory Management with Neo4j MCP

To prevent context window overflow when working with large amounts of data, the system uses Neo4j as a knowledge graph database for storing and retrieving AI assistant memories through the Neo4j MCP tool. This approach provides several benefits:

1. **Context Window Management**: When the context window approaches 60K tokens, the system automatically offloads less critical information to Neo4j, maintaining optimal performance.

2. **Knowledge Graph Structure**: Information is stored as entities and relationships, allowing for more nuanced understanding and retrieval compared to simple vector stores.

3. **Memory Persistence**: Important context is preserved across sessions, enabling the AI assistant to maintain continuity in long-running projects.

4. **Semantic Retrieval**: The graph structure allows for retrieving related concepts and context based on semantic relationships rather than just keyword matching.

#### Memory Management Workflow

1. **Context Monitoring**: The system continuously monitors the token count in the AI's context window.

2. **Threshold Detection**: When the context approaches 60K tokens, the memory management system is triggered.

3. **Priority Assessment**: Information is evaluated based on recency, relevance, and importance.

4. **Graph Storage**: Key entities, concepts, and their relationships are extracted and stored in the Neo4j graph using MCP tools.

5. **Context Pruning**: Less critical information is removed from the immediate context window.

6. **Just-in-time Retrieval**: When related topics arise in conversation, relevant information is retrieved from Neo4j and reintroduced to the context window.

#### Neo4j MCP Tools Reference

The Neo4j MCP integration provides the following tools for managing the knowledge graph:

##### Query Tools
- `mcp_neo4j_read_graph`: Read the entire knowledge graph
- `mcp_neo4j_search_nodes`: Search for nodes based on a query
- `mcp_neo4j_find_nodes`: Find specific nodes by name
- `mcp_neo4j_open_nodes`: Open specific nodes by name

##### Entity Management Tools
- `mcp_neo4j_create_entities`: Create multiple new entities in the knowledge graph
- `mcp_neo4j_delete_entities`: Delete multiple entities and their associated relations

##### Relation Management Tools
- `mcp_neo4j_create_relations`: Create multiple new relations between entities
- `mcp_neo4j_delete_relations`: Delete multiple relations from the graph

##### Observation Management Tools
- `mcp_neo4j_add_observations`: Add new observations to existing entities
- `mcp_neo4j_delete_observations`: Delete specific observations from entities

#### Neo4j MCP Usage Examples for Core Website Vitals

Here are practical examples of using Neo4j MCP tools with our Core Website Vitals project:

##### 1. Storing SEO Concepts and Relationships

```javascript
// Example: Storing key SEO concepts when context window gets large
mcp_neo4j_create_entities({
  entities: [
    {
      name: "Core Web Vitals",
      type: "SEO Concept",
      observations: [
        "Core Web Vitals are a set of specific factors that Google considers important in a webpage's overall user experience.",
        "They include Largest Contentful Paint (LCP), First Input Delay (FID), and Cumulative Layout Shift (CLS).",
        "They are part of Google's Page Experience signals used for ranking."
      ]
    },
    {
      name: "Largest Contentful Paint",
      type: "Performance Metric",
      observations: [
        "Measures loading performance - how quickly the largest content element becomes visible.",
        "Good LCP score is under 2.5 seconds.",
        "Affected by server response time, render-blocking resources, and resource load time."
      ]
    },
    {
      name: "OnPageAnalyzer",
      type: "Module",
      observations: [
        "Analyzes meta tags, heading structure, image SEO, link audit, and content quality.",
        "Implemented in modules/on_page_analyzer.py",
        "Contributes to the overall SEO score calculation."
      ]
    }
  ]
});

// Creating relationships between entities
mcp_neo4j_create_relations({
  relations: [
    {
      source: "Core Web Vitals",
      target: "Largest Contentful Paint",
      relationType: "INCLUDES"
    },
    {
      source: "OnPageAnalyzer",
      target: "Core Web Vitals",
      relationType: "ANALYZES"
    }
  ]
});
```

##### 2. Retrieving Context When Needed

```javascript
// Example: Searching for information about specific SEO concepts
const searchResults = mcp_neo4j_search_nodes({
  query: "Contentful Paint"
});

// Example: Finding specific modules when discussing implementation details
const moduleInfo = mcp_neo4j_find_nodes({
  names: ["OnPageAnalyzer", "TechnicalSEOAnalyzer"]
});
```

##### 3. Updating Knowledge as Project Evolves

```javascript
// Example: Adding new observations to existing entities as development progresses
mcp_neo4j_add_observations({
  observations: [
    {
      entityName: "OnPageAnalyzer",
      contents: [
        "Updated in PR #42 to include structured data validation.",
        "Now supports JSON-LD and Microdata formats for rich snippets."
      ]
    }
  ]
});

// Example: Creating new entities for new features
mcp_neo4j_create_entities({
  entities: [
    {
      name: "Historical Performance Tracking",
      type: "Feature",
      observations: [
        "Added in v2.0 to track SEO metrics over time.",
        "Stores historical data in Supabase with time-series visualization.",
        "Allows comparison of before/after changes to website."
      ]
    }
  ]
});

// Example: Creating relationships for new features
mcp_neo4j_create_relations({
  relations: [
    {
      source: "Historical Performance Tracking",
      target: "ScoringModule",
      relationType: "USES"
    }
  ]
});
```

##### 4. Cleaning Up Outdated Information

```javascript
// Example: Removing outdated observations
mcp_neo4j_delete_observations({
  deletions: [
    {
      entityName: "TechnicalSEOAnalyzer",
      observations: [
        "Currently limited to basic HTTP header checks.",
        "Planned expansion in v1.2 for more comprehensive analysis."
      ]
    }
  ]
});

// Example: Removing deprecated features
mcp_neo4j_delete_entities({
  entityNames: ["Legacy Report Generator"]
});

// Example: Removing outdated relationships
mcp_neo4j_delete_relations({
  relations: [
    {
      source: "ContentAnalyzer",
      target: "External API",
      relationType: "DEPENDS_ON"
    }
  ]
});
```

##### 5. Reading the Complete Knowledge Graph

```javascript
// Example: Reading the entire knowledge graph for comprehensive context
const fullGraph = mcp_neo4j_read_graph();
```

By using these Neo4j MCP tools, Claude can maintain context across long conversations about the Core Website Vitals project, even when the context window would otherwise be overwhelmed with information.

## Project Structure

```
corewebsitevitals/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── main.py            # FastAPI app initialization and middleware
│   │   ├── core/              # Core configuration and utilities
│   │   │   ├── config.py      # Pydantic settings (env vars, secrets)
│   │   │   ├── security.py    # JWT utilities, password hashing
│   │   │   └── supabase.py    # Supabase client configuration
│   │   ├── api/v1/            # API routes (versioned)
│   │   │   ├── router.py      # Main API router combining all endpoints
│   │   │   └── endpoints/     # Individual endpoint modules
│   │   │       ├── auth.py    # Authentication (login, register, refresh)
│   │   │       ├── analyses.py # Analysis CRUD operations
│   │   │       ├── dashboard.py # Dashboard aggregations and metrics
│   │   │       └── users.py   # User profile management
│   │   ├── models/            # Data models and schemas
│   │   │   ├── database.py    # Supabase table definitions and helpers
│   │   │   └── schemas.py     # Pydantic request/response models
│   │   ├── services/          # Business logic layer
│   │   │   ├── auth_service.py     # Authentication logic
│   │   │   ├── analysis_service.py # Analysis orchestration
│   │   │   ├── supabase_service.py # Database operations wrapper
│   │   │   └── seo_service.py      # SEO analyzer integration
│   │   └── worker/            # Celery background tasks
│   │       ├── celery_app.py  # Celery configuration and app instance
│   │       └── tasks.py       # Background task definitions
│   ├── tests/                 # Backend test suite
│   │   ├── unit/             # Unit tests for services and utilities
│   │   ├── integration/      # API endpoint integration tests
│   │   └── conftest.py       # Pytest fixtures and test configuration
│   ├── migrations/           # SQL migration files for Supabase
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container definition
├── frontend/                # Vue.js frontend application
│   ├── src/
│   │   ├── components/      # Reusable Vue components
│   │   │   ├── layout/      # AppHeader, AppSidebar, AppLayout
│   │   │   ├── forms/       # LoginForm, AnalysisForm, etc.
│   │   │   ├── dashboard/   # MetricCard, ScoreGauge, TrendChart
│   │   │   └── ui/          # BaseButton, BaseCard, BaseSpinner
│   │   ├── views/           # Page-level components (routes)
│   │   │   ├── HomeView.vue      # Landing page
│   │   │   ├── DashboardView.vue # Main dashboard
│   │   │   ├── AnalysisView.vue  # Individual analysis results
│   │   │   └── ProfileView.vue   # User profile management
│   │   ├── stores/          # Pinia state management
│   │   │   ├── auth.ts      # Authentication state and actions
│   │   │   ├── analysis.ts  # Analysis data and real-time updates
│   │   │   └── ui.ts        # UI state (modals, notifications)
│   │   ├── services/        # API and external service integration
│   │   │   ├── api.ts       # Axios configuration and interceptors
│   │   │   └── supabase.ts  # Supabase client for real-time features
│   │   ├── types/           # TypeScript type definitions
│   │   │   ├── api.types.ts # API request/response types
│   │   │   └── supabase.types.ts # Supabase generated types
│   │   ├── utils/           # Utility functions and helpers
│   │   └── router/          # Vue Router configuration
│   ├── public/             # Static assets and PWA manifest
│   ├── tests/              # Frontend test suite
│   │   ├── unit/           # Component unit tests
│   │   ├── integration/    # View integration tests
│   │   └── e2e/            # End-to-end tests with Playwright
│   ├── package.json        # Node.js dependencies and scripts
│   ├── vite.config.ts      # Vite build configuration
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── Dockerfile          # Frontend container definition
├── docker-compose.yml      # Multi-service development setup
├── .env.example           # Environment variable template
└── README.md              # Project documentation
```

## Core Business Logic

### SEO Analysis Workflow

1. **User submits URL** via dashboard form
2. **FastAPI creates task record** in Supabase with status 'PENDING'
3. **Celery task dispatched** to background worker via Redis
4. **Worker processes analysis** using integrated python-seo-analyzer
5. **Results stored** in Supabase JSONB column with status 'SUCCESS'
6. **Frontend receives updates** via real-time subscription or polling

### Key Data Models

```python
# Analysis Task Model (Supabase table: analysis_tasks)
{
    "id": "uuid",
    "user_id": "uuid",           # Links to auth.users
    "url_analyzed": "string",    # Target URL for analysis
    "status": "enum",            # PENDING, IN_PROGRESS, SUCCESS, FAILED
    "celery_task_id": "string",  # Celery task identifier
    "submitted_at": "timestamp",
    "completed_at": "timestamp",
    "results": "jsonb",          # Full SEO analysis results
    "error_message": "text"      # Error details if failed
}

# User Profile Model (Supabase table: profiles)
{
    "id": "uuid",                # Links to auth.users
    "email": "string",
    "full_name": "string",
    "subscription_tier": "enum", # free, pro, business, enterprise
    "created_at": "timestamp"
}
```

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account and project

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Required environment variables:
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-super-secret-key
```

### Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd corewebsitevitals

# 2. Start all services
docker-compose up -d

# 3. Run database migrations
# (Execute SQL files in migrations/ via Supabase dashboard)

# 4. Access applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Workflow

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
npm install
npm run dev

# Worker development
cd backend
celery -A app.worker.celery_app worker --loglevel=info

# Run tests
cd backend && python -m pytest tests/ -v
cd frontend && npm run test:unit
```

## Code Patterns and Conventions

### Backend Patterns

#### FastAPI Endpoint Pattern
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

#### Celery Task Pattern
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

#### Supabase Service Pattern
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

### Frontend Patterns

#### Pinia Store Pattern
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

#### Vue Component Pattern
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

## Database Schema

### Supabase Tables

```sql
-- User profiles (extends auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis tasks
CREATE TABLE public.analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    url_analyzed VARCHAR(2048) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    celery_task_id VARCHAR(255) UNIQUE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_message TEXT,
    analysis_type VARCHAR(50) DEFAULT 'full_seo'
);

-- Row Level Security Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own analysis tasks" ON public.analysis_tasks
    FOR SELECT USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_analysis_tasks_user_id_submitted_at 
    ON public.analysis_tasks(user_id, submitted_at DESC);
CREATE INDEX idx_analysis_tasks_status 
    ON public.analysis_tasks(status);
```

## API Reference

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/auth/register` | POST | User registration | No |
| `/api/v1/auth/login` | POST | User login | No |
| `/api/v1/auth/refresh` | POST | Token refresh | Yes |
| `/api/v1/auth/logout` | POST | User logout | Yes |

### Analysis Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/analyses/` | POST | Submit new analysis | Yes |
| `/api/v1/analyses/` | GET | List user analyses | Yes |
| `/api/v1/analyses/{id}` | GET | Get analysis details | Yes |
| `/api/v1/analyses/{id}` | DELETE | Cancel/delete analysis | Yes |

### Dashboard Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/dashboard/summary` | GET | Dashboard metrics | Yes |
| `/api/v1/dashboard/trends` | GET | Performance trends | Yes |

## Testing Guidelines

### Backend Testing

```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Run specific test categories
python -m pytest tests/unit/ -v           # Unit tests
python -m pytest tests/integration/ -v    # Integration tests

# Test with different markers
python -m pytest -m "not slow" -v         # Skip slow tests
python -m pytest -m "auth" -v             # Only auth tests
```

### Frontend Testing

```bash
# Unit tests
npm run test:unit

# Component tests
npm run test:component

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

### Test Patterns

#### Backend Test Pattern
```python
# tests/unit/test_analysis_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.analysis_service import AnalysisService

class TestAnalysisService:
    def setup_method(self):
        self.mock_supabase = Mock()
        self.service = AnalysisService(self.mock_supabase)
    
    @patch('app.services.seo_service.analyze_url')
    def test_submit_analysis_success(self, mock_analyze):
        # Arrange
        mock_analyze.return_value = {'score': 85}
        
        # Act
        result = self.service.submit_analysis('user-123', 'https://example.com')
        
        # Assert
        assert result['status'] == 'PENDING'
        self.mock_supabase.table.assert_called_with('analysis_tasks')
```

#### Frontend Test Pattern
```typescript
// tests/unit/stores/analysis.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAnalysisStore } from '@/stores/analysis'

describe('Analysis Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should submit analysis successfully', async () => {
    const store = useAnalysisStore()
    
    const result = await store.submitAnalysis('https://example.com')
    
    expect(result.url_analyzed).toBe('https://example.com')
    expect(store.analyses).toHaveLength(1)
  })
})
```

## Deployment

### Production Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Security
JWT_SECRET_KEY=your-production-secret-key
CORS_ORIGINS=https://corewebsitevitals.com

# Redis
REDIS_URL=redis://redis:6379/0

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=info

# Performance
CELERY_WORKER_CONCURRENCY=4
CELERY_MAX_RETRIES=3
```

### Docker Production Setup

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with environment file
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Scale workers based on load
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

## Troubleshooting

### Common Issues

#### Supabase Connection Issues
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Test connection
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"
```

#### Celery Worker Issues
```bash
# Check Redis connection
redis-cli ping

# Monitor Celery tasks
celery -A app.worker.celery_app inspect active

# Check worker logs
docker-compose logs worker
```

#### Authentication Issues
```bash
# Check JWT token validity
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/users/me

# Verify Supabase RLS policies
# Execute in Supabase SQL editor:
SELECT * FROM public.analysis_tasks; -- Should respect RLS
```

### Performance Monitoring

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/analyses/"

# Monitor database performance
# Use Supabase dashboard or pg_stat_statements

# Check memory usage
docker stats

# Monitor Celery queue length
celery -A app.worker.celery_app inspect stats
```

## Security Considerations

### Critical Security Practices

1. **Row Level Security (RLS)**: Always enable RLS on user data tables
2. **Input Validation**: Use Pydantic for all API inputs
3. **Environment Variables**: Never commit secrets to version control
4. **HTTPS Only**: Enforce HTTPS in production
5. **JWT Expiration**: Set appropriate token expiration times
6. **Rate Limiting**: Implement API rate limiting to prevent abuse

### Security Checklist

- [ ] RLS policies enabled on all user data tables
- [ ] JWT secret key is cryptographically secure
- [ ] All user inputs validated with Pydantic
- [ ] CORS configured properly for production domains
- [ ] Environment variables secured in production
- [ ] Dependency vulnerabilities scanned regularly
- [ ] Authentication endpoints rate limited
- [ ] Error messages don't leak sensitive information

## Contributing Guidelines

### Code Quality Standards

- **Python**: Follow PEP 8, use type hints, maintain >90% test coverage
- **TypeScript**: Strict mode enabled, explicit types, comprehensive testing
- **Commits**: Use conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- **PR Reviews**: Require approval from maintainer, all tests passing

### Development Workflow

1. Create feature branch from `main`
2. Implement changes with tests
3. Run linting and type checking
4. Submit PR with clear description
5. Address review feedback
6. Merge after approval

---

## Quick Reference

### Essential Commands

```bash
# Development
docker-compose up -d                    # Start all services
docker-compose logs -f backend          # View backend logs
docker-compose exec backend bash       # Access backend container

# Testing
python -m pytest tests/ -v             # Backend tests
npm run test:unit                       # Frontend tests

# Database
# Run migrations via Supabase dashboard
# Access: https://app.supabase.com/project/your-project-id/editor

# Deployment
docker-compose -f docker-compose.prod.yml up -d  # Production deployment
```

### Key File Locations

- **Backend Config**: `backend/app/core/config.py`
- **Database Models**: `backend/app/models/schemas.py`
- **API Routes**: `backend/app/api/v1/endpoints/`
- **Frontend Store**: `frontend/src/stores/`
- **Components**: `frontend/src/components/`
- **Environment**: `.env` (development), `.env.production` (production)

This CLAUDE.md provides comprehensive context for effective development and maintenance of the Core Website Vitals platform.