name: "Core Website Vitals - Transform SEO Analyzer to SaaS Platform"
description: |
  Transform the existing command-line python-seo-analyzer into corewebsitevitals.com, a full-stack SaaS platform with Vue.js frontend, FastAPI backend, Supabase database, and Celery workers for asynchronous SEO analysis.

---

## Goal

Transform the existing command-line python-seo-analyzer into a production-ready SaaS platform that provides:
- User authentication and multi-tenant data isolation using Supabase RLS
- Web-based dashboard for submitting URLs and viewing analysis results
- Asynchronous SEO analysis processing with real-time status updates
- Historical analysis tracking with data visualization
- RESTful API with comprehensive error handling and validation
- Scalable architecture supporting 1000+ concurrent analysis jobs

**End State**: A fully functional web application at corewebsitevitals.com where users can register, submit URLs for analysis, and view comprehensive SEO reports through an intuitive dashboard with real-time updates.

## Why

**Business Value:**
- Democratize advanced SEO analysis for non-technical users
- Create recurring revenue through subscription-based monitoring
- Establish competitive advantage through superior UX and real-time features
- Scale beyond single-user command-line tool to serve thousands of users

**User Impact:**
- Eliminate technical barriers to SEO analysis
- Provide actionable insights through data visualization
- Enable continuous website monitoring with historical trends
- Reduce time-to-insight from hours to minutes

**Integration Benefits:**
- Leverage existing python-seo-analyzer logic without rewriting core analysis
- Build on proven FastAPI + Vue.js technology stack
- Utilize Supabase for rapid development and built-in scalability

## What

### User-Visible Behavior

**Authentication Flow:**
- Users register with email/password or social login
- JWT-based session management with auto-refresh
- Profile management with subscription tier tracking

**Analysis Submission:**
- Simple URL input form with validation
- Immediate task creation with unique ID returned
- Real-time progress updates via WebSocket/polling
- Email notifications for completed analyses

**Dashboard Experience:**
- Clean overview with key metrics (score, issues, recommendations)
- Interactive charts showing score trends over time
- Detailed breakdown of technical SEO factors
- Historical analysis list with search/filter capabilities

### Technical Requirements

**Performance Targets:**
- API response time < 500ms for all endpoints
- Dashboard load time < 3 seconds
- Real-time updates with < 2 second latency
- Support 1000+ concurrent analysis jobs

**Security Standards:**
- HTTPS everywhere with proper certificate management
- Row-level security for multi-tenant data isolation
- Input validation and sanitization for all user data
- Rate limiting to prevent abuse

**Scalability Requirements:**
- Horizontal scaling for worker processes
- Database read replicas for reporting queries
- CDN integration for static assets
- Auto-scaling based on analysis queue depth

### Success Criteria

- [ ] User can register, login, and manage profile
- [ ] User can submit URL and receive analysis within 5 minutes
- [ ] Dashboard displays analysis results with interactive charts
- [ ] Historical data is preserved and searchable
- [ ] Real-time status updates work reliably
- [ ] All API endpoints return proper error messages
- [ ] Application handles 100+ concurrent users without degradation
- [ ] Test coverage > 90% across all components
- [ ] Zero critical security vulnerabilities in production

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://fastapi.tiangolo.com/tutorial/background-tasks/
  why: FastAPI background tasks patterns, dependency injection, async programming
  critical: Proper async/await patterns and BackgroundTasks vs Celery decision points
  
- url: https://testdriven.io/blog/fastapi-and-celery/
  why: FastAPI + Celery integration patterns, task routing, result backends
  critical: Proper serialization, retry mechanisms, monitoring setup

- url: https://supabase.com/docs/guides/database/postgres/row-level-security
  why: Supabase RLS implementation for multi-tenant applications
  critical: Policy creation, JWT claims, tenant isolation patterns
  
- url: https://supabase.com/docs/reference/python/introduction
  why: Supabase Python client patterns, real-time subscriptions, auth integration
  critical: Client initialization, error handling, async usage patterns

- url: https://pinia.vuejs.org/
  why: Vue.js 3 Composition API state management patterns
  critical: Modular store design, async actions, plugin system
  
- url: https://docs.celeryq.dev/en/stable/userguide/tasks.html
  why: Celery task patterns, retry mechanisms, error handling
  critical: Task serialization, exponential backoff, visibility timeout with Redis

- file: /Users/hiyabuddy/sites/trulyprivate/core-website-vitals/app.py
  why: Existing SEO analyzer main logic, module registration, Flask integration
  critical: SEOAnalyzer class structure, module pattern, configuration handling

- file: /Users/hiyabuddy/sites/trulyprivate/core-website-vitals/modules/base_module.py
  why: SEO module base class, common utilities, error handling patterns
  critical: Module interface, fetch_html pattern, configuration injection

- file: /Users/hiyabuddy/sites/trulyprivate/core-website-vitals/modules/on_page_analyzer.py
  why: Example SEO analysis module implementation
  critical: Analysis structure, result formatting, error handling

- file: /Users/hiyabuddy/sites/trulyprivate/core-website-vitals/modules/scoring_module.py
  why: SEO scoring logic, weight configuration, result aggregation
  critical: Scoring algorithm, configurable weights, result structure

- docfile: /Users/hiyabuddy/sites/trulyprivate/core-website-vitals/CLAUDE.md
  why: Project architecture, development patterns, security practices
  critical: Technology stack decisions, directory structure, validation commands
```

### Current Codebase Structure
```bash
core-website-vitals/
├── app.py                    # Main SEO analyzer with Flask API
├── modules/
│   ├── __init__.py
│   ├── base_module.py        # Abstract base class for SEO modules
│   ├── content_analyzer.py   # Content analysis (keywords, readability)
│   ├── on_page_analyzer.py   # Meta tags, headers, URL structure
│   ├── scoring_module.py     # Scoring algorithm and weights
│   └── technical_seo_analyzer.py  # Technical SEO (SSL, robots, sitemap)
├── requirements.txt          # Basic dependencies (requests, BeautifulSoup, Flask)
├── CLAUDE.md                 # Project architecture and patterns
├── PRPs/
│   └── templates/
│       └── prp_base.md      # PRP template structure
└── README.md
```

### Desired Full-Stack Architecture
```bash
corewebsitevitals/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── main.py            # FastAPI app initialization, middleware, CORS
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic settings (Supabase, Redis, JWT)
│   │   │   ├── security.py    # JWT utilities, password hashing
│   │   │   └── supabase.py    # Supabase client configuration
│   │   ├── api/v1/            # API routes (versioned)
│   │   │   ├── router.py      # Main API router combining all endpoints
│   │   │   └── endpoints/     # Individual endpoint modules
│   │   │       ├── auth.py    # Authentication (login, register, refresh)
│   │   │       ├── analyses.py # Analysis CRUD operations
│   │   │       ├── dashboard.py # Dashboard aggregations and metrics
│   │   │       └── users.py   # User profile management
│   │   ├── models/
│   │   │   ├── database.py    # Supabase table definitions and helpers
│   │   │   └── schemas.py     # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── auth_service.py     # Authentication logic
│   │   │   ├── analysis_service.py # Analysis orchestration
│   │   │   ├── supabase_service.py # Database operations wrapper
│   │   │   └── seo_service.py      # SEO analyzer integration wrapper
│   │   └── worker/
│   │       ├── celery_app.py       # Celery configuration and app instance
│   │       └── tasks.py            # Background task definitions
│   ├── tests/                     # Backend test suite
│   │   ├── unit/                  # Unit tests for services and utilities
│   │   ├── integration/           # API endpoint integration tests
│   │   └── conftest.py            # Pytest fixtures and configuration
│   ├── migrations/                # SQL migration files for Supabase
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Backend container definition
├── frontend/                      # Vue.js frontend application
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/           # AppHeader, AppSidebar, AppLayout
│   │   │   ├── forms/            # LoginForm, AnalysisForm, etc.
│   │   │   ├── dashboard/        # MetricCard, ScoreGauge, TrendChart
│   │   │   └── ui/               # BaseButton, BaseCard, BaseSpinner
│   │   ├── views/
│   │   │   ├── HomeView.vue      # Landing page
│   │   │   ├── DashboardView.vue # Main dashboard
│   │   │   ├── AnalysisView.vue  # Individual analysis results
│   │   │   └── ProfileView.vue   # User profile management
│   │   ├── stores/
│   │   │   ├── auth.ts           # Authentication state and actions
│   │   │   ├── analysis.ts       # Analysis data and real-time updates
│   │   │   └── ui.ts             # UI state (modals, notifications)
│   │   ├── services/
│   │   │   ├── api.ts            # Axios configuration and interceptors
│   │   │   └── supabase.ts       # Supabase client for real-time features
│   │   ├── types/
│   │   │   ├── api.types.ts      # API request/response types
│   │   │   └── supabase.types.ts # Supabase generated types
│   │   ├── utils/                # Utility functions and helpers
│   │   └── router/               # Vue Router configuration
│   ├── public/                   # Static assets and PWA manifest
│   ├── tests/                    # Frontend test suite
│   │   ├── unit/                 # Component unit tests
│   │   ├── integration/          # View integration tests
│   │   └── e2e/                  # End-to-end tests
│   ├── package.json              # Node.js dependencies and scripts
│   ├── vite.config.ts            # Vite build configuration
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   └── Dockerfile                # Frontend container definition
├── docker-compose.yml            # Multi-service development setup
├── .env.example                  # Environment variable template
└── README.md                     # Project documentation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Supabase requires proper RLS policies for multi-tenant security
# Row Level Security must be enabled on ALL user data tables
# Example: CREATE POLICY "Users see own data" ON analysis_tasks FOR SELECT USING (auth.uid() = user_id);

# CRITICAL: Celery requires explicit JSON serialization for task arguments
# Don't pass complex objects directly - serialize to dict/JSON first
# Example: perform_analysis.delay(task_id=str(uuid), url=url_string)
# With Redis: visibility_timeout defaults to 1 hour - tasks must complete within this time

# CRITICAL: FastAPI async functions must use await for database operations
# Mixing sync/async code will cause blocking and poor performance
# Example: response = await supabase.table('analysis_tasks').select('*').execute()

# CRITICAL: Vue.js reactive references need .value in composition API
# Forgetting .value causes silent failures in reactive updates
# Example: const count = ref(0); count.value = 1  # NOT count = 1

# CRITICAL: Supabase real-time requires specific channel subscription patterns
# Incorrect filter syntax will cause silent subscription failures
# Example: filter: `user_id=eq.${userId}` NOT filter: `user_id=${userId}`

# CRITICAL: python-seo-analyzer may have network timeouts on slow sites
# Wrap in try/catch and implement retry logic with exponential backoff
# Default timeout may be too short for large websites
# Current modules use requests.get() with timeout from global config

# CRITICAL: JWT tokens need proper expiration and refresh handling
# Expired tokens cause 401 errors - implement automatic refresh
# Store refresh tokens securely and handle refresh failures gracefully

# CRITICAL: Existing SEO modules expect sync execution
# Need to wrap existing analysis code in async functions for Celery workers
# Example: asyncio.run_in_executor() or run_in_threadpool()
```

## Implementation Blueprint

### Data Models and Structure

```python
# Supabase Table Definitions (migrations/001_initial_schema.sql)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own analysis tasks" ON public.analysis_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own analysis tasks" ON public.analysis_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX idx_analysis_tasks_user_id_submitted_at 
    ON public.analysis_tasks(user_id, submitted_at DESC);
CREATE INDEX idx_analysis_tasks_status 
    ON public.analysis_tasks(status);
CREATE INDEX idx_analysis_tasks_celery_task_id 
    ON public.analysis_tasks(celery_task_id);

# Pydantic Schemas (app/models/schemas.py)
class AnalysisTaskCreate(BaseModel):
    url: HttpUrl
    analysis_type: str = "full_seo"

class AnalysisTaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    url_analyzed: str
    status: str
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: str = "free"
    created_at: datetime
    updated_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
```

### List of Implementation Tasks

```yaml
Task 1 - Project Setup & Environment:
  CREATE backend/app/ directory structure:
    - SETUP FastAPI project with proper module organization
    - CREATE requirements.txt with FastAPI, Supabase, Celery, Redis dependencies
    - CREATE .env.example with all required environment variables
    - SETUP proper Python project structure with __init__.py files
  
  CREATE migrations/001_initial_schema.sql:
    - DEFINE profiles and analysis_tasks tables
    - IMPLEMENT Row Level Security policies for multi-tenant isolation
    - CREATE proper indexes for performance optimization
    - SETUP foreign key relationships and constraints

Task 2 - Backend Core Configuration:
  CREATE backend/app/core/config.py:
    - IMPLEMENT Pydantic Settings for environment variable management
    - CONFIGURE Supabase URL, keys, and connection settings
    - SETUP Redis URL and Celery configuration
    - DEFINE JWT settings and security configurations
  
  CREATE backend/app/core/supabase.py:
    - IMPLEMENT create_supabase_client() function for regular operations
    - SETUP create_supabase_admin_client() for service operations
    - CONFIGURE connection pooling and error handling
    - IMPLEMENT proper client initialization patterns

Task 3 - Authentication System:
  CREATE backend/app/core/security.py:
    - IMPLEMENT JWT token creation and validation utilities
    - SETUP password hashing with bcrypt
    - CREATE token refresh mechanism
    - IMPLEMENT security dependencies for FastAPI
  
  CREATE backend/app/services/auth_service.py:
    - IMPLEMENT user registration with Supabase Auth
    - CREATE login logic with JWT token generation
    - SETUP profile creation and management
    - IMPLEMENT token refresh and logout functionality
  
  CREATE backend/app/api/v1/endpoints/auth.py:
    - IMPLEMENT /register endpoint with proper validation
    - CREATE /login endpoint with error handling
    - SETUP /refresh endpoint for token renewal
    - IMPLEMENT /logout endpoint with token invalidation

Task 4 - Database Service Layer:
  CREATE backend/app/services/supabase_service.py:
    - IMPLEMENT SupabaseService class with CRUD operations
    - CREATE methods for analysis_tasks table operations
    - SETUP proper error handling for database operations
    - IMPLEMENT connection retry logic and timeout handling
  
  CREATE backend/app/models/database.py:
    - DEFINE table helper functions and utilities
    - IMPLEMENT database connection management
    - CREATE query builders for complex operations
    - SETUP proper type hints and error handling

Task 5 - SEO Analysis Service Integration:
  CREATE backend/app/services/seo_service.py:
    - WRAP existing SEO analyzer modules (OnPageAnalyzer, TechnicalSEOAnalyzer, etc.)
    - IMPLEMENT async wrapper for sync SEO analysis code
    - CREATE proper error handling and timeout management
    - SETUP result formatting and normalization
  
  MODIFY existing modules for service integration:
    - PRESERVE existing analysis logic in modules/
    - CREATE async wrappers using run_in_threadpool or asyncio.run_in_executor
    - IMPLEMENT proper error propagation and logging
    - SETUP configuration injection for analysis parameters

Task 6 - Celery Worker System:
  CREATE backend/app/worker/celery_app.py:
    - CONFIGURE Celery with Redis broker and result backend
    - SETUP proper serialization (JSON) and task routing
    - IMPLEMENT monitoring and logging configuration
    - CREATE worker configuration for scaling
  
  CREATE backend/app/worker/tasks.py:
    - IMPLEMENT perform_seo_analysis task with proper error handling
    - UPDATE analysis_tasks status throughout task execution
    - SETUP retry logic with exponential backoff
    - IMPLEMENT proper result storage and error reporting

Task 7 - Analysis API Endpoints:
  CREATE backend/app/services/analysis_service.py:
    - IMPLEMENT analysis orchestration logic
    - CREATE task submission and status tracking
    - SETUP proper validation and error handling
    - IMPLEMENT result retrieval and formatting
  
  CREATE backend/app/api/v1/endpoints/analyses.py:
    - IMPLEMENT POST /analyses/ for analysis submission
    - CREATE GET /analyses/ for user's analysis list with pagination
    - SETUP GET /analyses/{id} for detailed results
    - IMPLEMENT DELETE /analyses/{id} for task cancellation

Task 8 - Frontend Vue.js Foundation:
  CREATE frontend/ project structure:
    - INITIALIZE Vue 3 + TypeScript + Vite project
    - SETUP package.json with Vue Router, Pinia, Axios, Chart.js
    - CONFIGURE Tailwind CSS for styling
    - SETUP proper build configuration and development server
  
  CREATE frontend/src/services/api.ts:
    - CONFIGURE Axios with base URL and interceptors
    - IMPLEMENT request/response interceptors for authentication
    - SETUP error handling and retry logic
    - CREATE API method definitions for all endpoints

Task 9 - Frontend Authentication:
  CREATE frontend/src/stores/auth.ts:
    - IMPLEMENT Pinia store for authentication state
    - SETUP login, register, logout actions
    - MANAGE JWT token persistence in localStorage
    - IMPLEMENT automatic token refresh logic
  
  CREATE frontend/src/components/forms/LoginForm.vue:
    - BUILD reactive form with proper validation
    - CONNECT to auth store actions
    - IMPLEMENT error handling and loading states
    - SETUP proper form submission and navigation

Task 10 - Frontend Analysis Management:
  CREATE frontend/src/stores/analysis.ts:
    - IMPLEMENT analysis data management with Pinia
    - SETUP real-time subscriptions for status updates
    - IMPLEMENT polling fallback for older browsers
    - MANAGE analysis history and pagination
  
  CREATE frontend/src/components/forms/AnalysisForm.vue:
    - IMPLEMENT URL input with proper validation
    - CONNECT to analysis submission API
    - SHOW immediate feedback and loading states
    - IMPLEMENT proper error handling and user feedback

Task 11 - Real-time Updates System:
  CREATE frontend/src/services/supabase.ts:
    - CONFIGURE Supabase client for real-time subscriptions
    - IMPLEMENT authentication state management
    - SETUP channel subscriptions for analysis updates
    - IMPLEMENT connection error handling and reconnection

Task 12 - Dashboard & Visualization:
  CREATE frontend/src/components/dashboard/ScoreGauge.vue:
    - BUILD Chart.js gauge component for SEO scores
    - IMPLEMENT responsive design and accessibility
    - SETUP proper data visualization patterns
    - CREATE reusable chart components
  
  CREATE frontend/src/views/DashboardView.vue:
    - IMPLEMENT main dashboard layout and components
    - CONNECT to analysis store for data display
    - SETUP real-time updates and data refresh
    - IMPLEMENT proper loading and error states

Task 13 - Docker & Deployment Setup:
  CREATE docker-compose.yml:
    - DEFINE services: frontend, backend, worker, redis, postgres
    - SETUP proper networking and volume mounts
    - CONFIGURE environment variable passing
    - IMPLEMENT health checks and restart policies
  
  CREATE Dockerfiles:
    - OPTIMIZE backend Dockerfile for Python/FastAPI
    - BUILD frontend Dockerfile for Vue.js production
    - IMPLEMENT multi-stage builds for smaller images
    - SETUP proper security practices and non-root users
```

### Critical Implementation Pseudocode

```python
# Task 6 - Celery Worker Implementation
@celery_app.task(bind=True, name='tasks.perform_seo_analysis', autoretry_for=(Exception,))
def perform_seo_analysis(self, analysis_task_id: str, url: str):
    """
    Background task for SEO analysis with proper error handling and retries.
    CRITICAL: Must update database status throughout execution.
    """
    # PATTERN: Always update status first
    supabase_service = SupabaseService(supabase_admin_client)
    
    try:
        # CRITICAL: Update to IN_PROGRESS immediately
        supabase_service.update_analysis_task(
            task_id=analysis_task_id,
            updates={
                'status': 'IN_PROGRESS',
                'started_at': datetime.utcnow().isoformat(),
                'celery_task_id': self.request.id
            }
        )
        
        # PATTERN: Use service layer abstraction
        seo_service = SeoAnalysisService()
        
        # GOTCHA: Wrap existing sync code in async executor
        # Existing modules use sync requests - need proper async wrapping
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # CRITICAL: Implement timeout to prevent hanging
        try:
            # Use existing SEOAnalyzer class with timeout
            analyzer = SEOAnalyzer(url, config=get_analysis_config())
            
            # GOTCHA: run_analysis is sync - wrap it properly
            results = await loop.run_in_executor(
                None, 
                analyzer.run_analysis, 
                url, 
                None,  # cli_keywords
                None   # custom_module_config
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"Analysis timeout for {url}")
        finally:
            loop.close()
        
        # CRITICAL: Store results atomically
        supabase_service.update_analysis_task(
            task_id=analysis_task_id,
            updates={
                'status': 'SUCCESS',
                'results': results,
                'completed_at': datetime.utcnow().isoformat()
            }
        )
        
        return {'status': 'SUCCESS', 'task_id': analysis_task_id}
        
    except Exception as e:
        # PATTERN: Always log errors and update status
        logger.error(f"Analysis failed for {analysis_task_id}: {str(e)}")
        
        supabase_service.update_analysis_task(
            task_id=analysis_task_id,
            updates={
                'status': 'FAILED',
                'error_message': str(e),
                'completed_at': datetime.utcnow().isoformat()
            }
        )
        
        # CRITICAL: Retry with exponential backoff
        # Redis visibility_timeout is 1 hour by default
        raise self.retry(
            exc=e, 
            countdown=60 * (2 ** self.request.retries), 
            max_retries=3
        )

# Task 10 - Real-time Updates Implementation
def subscribeToAnalysisUpdates(userId: string) {
    // PATTERN: Use specific channel naming for user isolation
    const subscription = supabase
        .channel(`analysis_tasks:${userId}`)
        .on(
            'postgres_changes',
            {
                event: 'UPDATE',
                schema: 'public',
                table: 'analysis_tasks',
                filter: `user_id=eq.${userId}`  // CRITICAL: Exact syntax required
            },
            (payload) => {
                // PATTERN: Update local state reactively
                const updatedTask = payload.new
                const index = analyses.value.findIndex(a => a.id === updatedTask.id)
                
                if (index !== -1) {
                    // GOTCHA: Must use .value for reactive updates
                    analyses.value[index] = updatedTask
                }
                
                // PATTERN: Handle completion notifications
                if (updatedTask.status === 'SUCCESS') {
                    showNotification('Analysis completed successfully!', 'success')
                } else if (updatedTask.status === 'FAILED') {
                    showNotification('Analysis failed. Please try again.', 'error')
                }
            }
        )
        .subscribe()
    
    // PATTERN: Return subscription for cleanup
    return subscription
}

# Task 3 - Authentication Service Implementation
class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def register_user(self, email: str, password: str, full_name: str = None):
        """
        Register new user with Supabase Auth and create profile.
        CRITICAL: Must create profile record after user creation.
        """
        try:
            # PATTERN: Use Supabase Auth for user creation
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if auth_response.user:
                # CRITICAL: Create profile record for RLS
                profile_data = {
                    "id": auth_response.user.id,
                    "email": email,
                    "full_name": full_name,
                    "subscription_tier": "free"
                }
                
                profile_response = self.supabase.table('profiles').insert(profile_data).execute()
                
                if not profile_response.data:
                    raise Exception("Failed to create user profile")
                
                return {
                    "user": auth_response.user,
                    "profile": profile_response.data[0]
                }
            else:
                raise Exception("User registration failed")
                
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Registration failed: {str(e)}"
            )
```

### Integration Points

```yaml
SUPABASE:
  - configuration: "Set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"
  - migrations: "Run SQL files in migrations/ directory via Supabase dashboard"
  - RLS: "Enable Row Level Security on profiles and analysis_tasks tables"
  - auth: "Configure JWT settings and custom claims for tenant isolation"

CELERY:
  - broker: "Configure Redis URL for task queue (default: redis://localhost:6379/0)"
  - monitoring: "Use Flower for task monitoring in development"
  - scaling: "Scale workers horizontally based on analysis_tasks queue depth"
  - serialization: "Use JSON serialization for all task arguments"

FRONTEND:
  - api: "Configure VITE_API_URL to point to FastAPI backend"
  - supabase: "Configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY"
  - routing: "Setup Vue Router with authentication guards"
  - real-time: "Setup Supabase real-time subscriptions for analysis updates"

EXISTING_SEO_MODULES:
  - integration: "Wrap existing modules (OnPageAnalyzer, TechnicalSEOAnalyzer, etc.) in async service"
  - configuration: "Pass analysis configuration from database to modules"
  - error_handling: "Implement proper error propagation from modules to Celery tasks"
  - results: "Normalize module results for consistent API responses"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Backend validation - run these FIRST
cd backend
ruff check app/ --fix
black app/
mypy app/

# Frontend validation
cd frontend  
npm run lint -- --fix
npm run type-check
npm run build  # Ensure it builds without errors

# Expected: No errors. If errors exist, READ them carefully and fix before proceeding.
```

### Level 2: Unit Tests
```python
# Backend Unit Tests - CREATE comprehensive test coverage

# test_supabase_service.py
def test_create_analysis_task():
    """Test creating analysis task creates record with correct data"""
    service = SupabaseService(mock_supabase_client)
    task_data = {
        "url_analyzed": "https://example.com",
        "user_id": "user-123",
        "status": "PENDING"
    }
    
    result = service.create_analysis_task(task_data)
    
    assert result['url_analyzed'] == "https://example.com"
    assert result['status'] == 'PENDING'
    assert result['user_id'] == "user-123"
    assert 'id' in result

def test_update_analysis_task():
    """Test updating task status works correctly"""
    service = SupabaseService(mock_supabase_client)
    
    result = service.update_analysis_task(
        "task-123", 
        {"status": "SUCCESS", "results": {"overall_score": 85}}
    )
    
    assert result['status'] == 'SUCCESS'
    assert result['results']['overall_score'] == 85

# test_seo_service.py
def test_seo_analysis_integration():
    """Test SEO analysis service wraps existing modules correctly"""
    seo_service = SeoAnalysisService()
    
    # Mock the existing analyzer
    with patch('app.services.seo_service.SEOAnalyzer') as mock_analyzer:
        mock_analyzer.return_value.run_analysis.return_value = {
            "seo_attributes": {
                "OnPageAnalyzer": {"title_score": 85},
                "TechnicalSEOAnalyzer": {"https_score": 100}
            }
        }
        
        result = seo_service.analyze_url("https://example.com")
        
        assert "seo_attributes" in result
        assert result["seo_attributes"]["OnPageAnalyzer"]["title_score"] == 85

# test_celery_tasks.py
def test_perform_seo_analysis_success():
    """Test successful SEO analysis task execution"""
    with patch('app.worker.tasks.SupabaseService') as mock_service:
        with patch('app.worker.tasks.SeoAnalysisService') as mock_seo:
            mock_seo.return_value.analyze_url.return_value = {"score": 85}
            
            result = perform_seo_analysis.apply(
                args=["task-123", "https://example.com"]
            )
            
            assert result.get()['status'] == 'SUCCESS'
            # Verify database updates were called
            mock_service.return_value.update_analysis_task.assert_called()

# Frontend Unit Tests - CREATE Vue component tests

# stores/auth.test.ts
describe('Auth Store', () => {
  it('should login successfully and store user data', async () => {
    const authStore = useAuthStore()
    
    // Mock successful login
    vi.mocked(api.post).mockResolvedValue({
      data: {
        access_token: 'mock-token',
        user: { id: '123', email: 'test@example.com' }
      }
    })
    
    await authStore.login({
      email: 'test@example.com',
      password: 'password123'
    })
    
    expect(authStore.isAuthenticated).toBe(true)
    expect(authStore.user?.email).toBe('test@example.com')
  })
  
  it('should handle login errors gracefully', async () => {
    const authStore = useAuthStore()
    
    vi.mocked(api.post).mockRejectedValue(new Error('Invalid credentials'))
    
    await expect(authStore.login({
      email: 'invalid@example.com',
      password: 'wrongpassword'
    })).rejects.toThrow('Invalid credentials')
    
    expect(authStore.isAuthenticated).toBe(false)
  })
})

# stores/analysis.test.ts
describe('Analysis Store', () => {
  it('should submit analysis and update store state', async () => {
    const analysisStore = useAnalysisStore()
    
    vi.mocked(api.post).mockResolvedValue({
      data: {
        id: 'task-123',
        status: 'PENDING',
        url_analyzed: 'https://example.com'
      }
    })
    
    await analysisStore.submitAnalysis('https://example.com')
    
    expect(analysisStore.analyses).toHaveLength(1)
    expect(analysisStore.analyses[0].status).toBe('PENDING')
  })
})
```

```bash
# Run and iterate until passing
cd backend && python -m pytest tests/ -v --cov=app --cov-report=html
cd frontend && npm run test:unit

# If failing: Read error messages, understand root cause, fix code, re-run
# NEVER mock away real failures - fix the underlying issue
```

### Level 3: Integration Tests
```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Test backend API endpoints
# 1. Test user registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# Expected: 201 Created with user object and access tokens

# 2. Test user login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Expected: 200 OK with access_token and refresh_token

# 3. Test analysis submission (replace TOKEN with actual token from login)
curl -X POST http://localhost:8000/api/v1/analyses/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"url": "https://example.com"}'

# Expected: 202 Accepted with task_id and PENDING status

# 4. Test analysis status check
curl -X GET http://localhost:8000/api/v1/analyses/TASK_ID \
  -H "Authorization: Bearer TOKEN"

# Expected: 200 OK with analysis task details

# 5. Test frontend loads
curl -I http://localhost:3000
# Expected: 200 OK with proper headers

# 6. Check logs for errors
docker-compose logs backend | grep ERROR
docker-compose logs worker | grep ERROR
docker-compose logs frontend | grep ERROR

# If errors: Check application logs, fix issues, restart services
```

## Final Validation Checklist

- [ ] All unit tests pass: `cd backend && python -m pytest tests/ -v --cov=app`
- [ ] All frontend tests pass: `cd frontend && npm run test:unit`
- [ ] No linting errors: `cd backend && ruff check app/` and `cd frontend && npm run lint`
- [ ] No type errors: `cd backend && mypy app/` and `cd frontend && npm run type-check`
- [ ] Docker services start successfully: `docker-compose up -d`
- [ ] User registration/login works via API and returns proper tokens
- [ ] Analysis submission returns task_id immediately and queues Celery task
- [ ] Celery worker processes tasks and updates database status
- [ ] Frontend dashboard loads and displays analysis data
- [ ] Real-time updates work when analysis status changes
- [ ] Error cases return proper HTTP status codes and messages
- [ ] Database has proper RLS policies enabled and working
- [ ] All environment variables are documented in .env.example
- [ ] Existing SEO analysis modules integrate properly with new architecture
- [ ] Performance targets met: API < 500ms, dashboard < 3s load time

---

## Anti-Patterns to Avoid

- ❌ **Don't use sync database calls in async FastAPI endpoints** - causes blocking and poor performance
- ❌ **Don't skip Row Level Security policies** - creates security vulnerabilities for multi-tenant data
- ❌ **Don't pass complex objects to Celery tasks** - causes serialization errors, use JSON-serializable data
- ❌ **Don't forget .value when updating Vue refs** - breaks reactivity in Composition API
- ❌ **Don't hardcode Supabase credentials** - use environment variables and proper configuration
- ❌ **Don't ignore Celery task failures** - implement proper retry logic with exponential backoff
- ❌ **Don't mix authentication methods** - use Supabase Auth consistently across frontend and backend
- ❌ **Don't skip input validation** - validate all user inputs with Pydantic schemas
- ❌ **Don't block the main thread** - use background tasks for SEO analysis operations
- ❌ **Don't assume network requests succeed** - wrap existing SEO modules in proper timeout and error handling
- ❌ **Don't modify existing SEO analysis logic** - wrap it in service layer to preserve working functionality
- ❌ **Don't ignore Redis visibility_timeout** - ensure Celery tasks complete within 1 hour default limit

**Critical Success Factor**: Follow the validation loops strictly. Each level must pass before proceeding to the next. This ensures working code at every step and successful transformation of the command-line tool into a full-stack SaaS platform.