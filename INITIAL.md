# Core Website Vitals - PRP v2 Implementation Guide

**name**: "Core Website Vitals - Transform SEO Analyzer to SaaS Platform"  
**description**: Transform the ihuzaifashoukat/seo-analyzer Python library into corewebsitevitals.com, a full-stack SaaS platform with Vue.js frontend, FastAPI backend, Supabase database, and Celery workers for asynchronous SEO analysis.

---

## Goal

Transform the command-line python-seo-analyzer into a production-ready SaaS platform that provides:
- User authentication and multi-tenant data isolation
- Web-based dashboard for submitting URLs and viewing analysis results
- Asynchronous SEO analysis processing with real-time status updates
- Historical analysis tracking with data visualization
- RESTful API with comprehensive error handling and validation

**End State**: A fully functional web application at corewebsitevitals.com where users can register, submit URLs for analysis, and view comprehensive SEO reports through an intuitive dashboard.

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

**Reporting Features:**
- Comprehensive SEO audit reports
- Exportable PDF summaries
- Shareable public links for client presentations
- Automated recommendations with priority levels

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
- url: https://fastapi.tiangolo.com/
  why: FastAPI framework patterns, dependency injection, background tasks
  critical: Async programming model, dependency injection for database sessions

- url: https://supabase.com/docs/reference/python/introduction
  why: Supabase Python client patterns, real-time subscriptions, RLS policies
  critical: Row Level Security setup for multi-tenant applications

- url: https://vuejs.org/guide/
  why: Vue.js 3 composition API, component architecture, state management
  section: Composition API, Pinia state management patterns

- url: https://docs.celeryproject.org/en/stable/
  why: Celery task patterns, error handling, retry mechanisms
  critical: Task routing, result backends, monitoring

- url: https://pydantic-docs.helpmanual.io/
  why: Data validation patterns, schema design, type safety
  section: Custom validators, nested models, serialization

- file: https://github.com/ihuzaifashoukat/seo-analyzer
  why: Understand existing analysis functions, input/output formats
  critical: Integration patterns, error handling, performance considerations

- docfile: Base PRP Template v2
  why: Implementation patterns, validation loops, anti-patterns to avoid
```

### Current Codebase Tree

```bash
# Run this in the seo-analyzer repository root
tree -I '__pycache__|*.pyc|.git' --dirsfirst -L 3
```

### Desired Codebase Tree

```bash
corewebsitevitals/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app initialization
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic settings
│   │   │   ├── security.py            # JWT utilities
│   │   │   └── supabase.py            # Supabase client setup
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py          # Main API router
│   │   │       └── endpoints/
│   │   │           ├── auth.py        # Authentication routes
│   │   │           ├── analyses.py    # Analysis CRUD operations
│   │   │           └── dashboard.py   # Dashboard aggregations
│   │   ├── models/
│   │   │   ├── database.py           # Supabase table definitions
│   │   │   └── schemas.py            # Pydantic models
│   │   ├── services/
│   │   │   ├── auth_service.py       # Authentication logic
│   │   │   ├── analysis_service.py   # Analysis orchestration
│   │   │   ├── supabase_service.py   # Database operations
│   │   │   └── seo_service.py        # SEO analyzer wrapper
│   │   └── worker/
│   │       ├── celery_app.py         # Celery configuration
│   │       └── tasks.py              # Background tasks
│   ├── tests/
│   ├── migrations/                   # SQL migration files
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/              # AppHeader, AppSidebar, AppLayout
│   │   │   ├── forms/               # LoginForm, AnalysisForm
│   │   │   ├── dashboard/           # MetricCard, ScoreGauge, TrendChart
│   │   │   └── ui/                  # BaseButton, BaseCard, BaseSpinner
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── DashboardView.vue
│   │   │   └── AnalysisView.vue
│   │   ├── stores/
│   │   │   ├── auth.ts              # Authentication state
│   │   │   └── analysis.ts          # Analysis data management
│   │   ├── services/
│   │   │   ├── api.ts               # Axios configuration
│   │   │   └── supabase.ts          # Supabase client
│   │   └── types/
│   │       └── api.types.ts         # TypeScript interfaces
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Supabase requires proper RLS policies for multi-tenant security
# Row Level Security must be enabled on ALL user data tables
# Example: CREATE POLICY "Users see own data" ON analysis_tasks FOR SELECT USING (auth.uid() = user_id);

# CRITICAL: Celery requires explicit JSON serialization for task arguments
# Don't pass complex objects directly - serialize to dict/JSON first
# Example: perform_analysis.delay(task_id=str(uuid), url=url_string)

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

# CRITICAL: JWT tokens need proper expiration and refresh handling
# Expired tokens cause 401 errors - implement automatic refresh
# Store refresh tokens securely and handle refresh failures gracefully
```

## Implementation Blueprint

### Data Models and Structure

```python
# Supabase Table Definitions (migrations/001_initial_schema.sql)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE public.analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    url_analyzed VARCHAR(2048) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    celery_task_id VARCHAR(255) UNIQUE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_message TEXT
);

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
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    subscription_tier: str = "free"
    created_at: datetime
```

### List of Implementation Tasks

```yaml
Task 1 - Project Setup:
  MODIFY backend/ directory:
    - CREATE app/ with proper structure
    - INJECT requirements.txt with FastAPI, Supabase, Celery dependencies
    - CREATE .env.example with all required environment variables
  
  CREATE migrations/001_initial_schema.sql:
    - DEFINE profiles and analysis_tasks tables
    - IMPLEMENT Row Level Security policies
    - CREATE proper indexes for performance

Task 2 - Supabase Integration:
  CREATE app/core/supabase.py:
    - IMPLEMENT create_supabase_client() function
    - CONFIGURE connection with environment variables
    - SETUP admin client for worker operations
  
  CREATE app/services/supabase_service.py:
    - IMPLEMENT SupabaseService class with CRUD operations
    - MIRROR patterns from Supabase documentation
    - PRESERVE error handling for connection failures

Task 3 - Authentication System:
  CREATE app/services/auth_service.py:
    - IMPLEMENT Supabase Auth integration OR custom JWT
    - FIND pattern in FastAPI security documentation
    - INJECT proper password hashing with bcrypt

  CREATE app/api/v1/endpoints/auth.py:
    - IMPLEMENT /register and /login endpoints
    - FOLLOW OAuth2PasswordBearer pattern for protected routes
    - PRESERVE proper error responses and validation

Task 4 - Analysis API Endpoints:
  CREATE app/services/seo_service.py:
    - WRAP python-seo-analyzer library calls
    - IMPLEMENT proper error handling and timeouts
    - KEEP abstraction layer for future library updates

  CREATE app/api/v1/endpoints/analyses.py:
    - IMPLEMENT POST /analyses/ for submission
    - IMPLEMENT GET /analyses/ for user's analysis list
    - IMPLEMENT GET /analyses/{id} for detailed results
    - FOLLOW RESTful patterns with proper status codes

Task 5 - Celery Worker System:
  CREATE app/worker/celery_app.py:
    - CONFIGURE Celery with Redis broker
    - SETUP proper serialization and error handling
    - MIRROR Celery best practices documentation

  CREATE app/worker/tasks.py:
    - IMPLEMENT perform_seo_analysis task
    - UPDATE analysis_tasks status throughout execution
    - HANDLE errors gracefully with retry logic

Task 6 - Frontend Vue.js Setup:
  CREATE frontend/ structure:
    - INITIALIZE Vue 3 + TypeScript + Vite project
    - INJECT package.json with Vue Router, Pinia, Chart.js
    - SETUP Tailwind CSS for styling

  CREATE src/services/supabase.ts:
    - CONFIGURE Supabase client for frontend
    - IMPLEMENT authentication state management
    - SETUP real-time subscriptions

Task 7 - Authentication Frontend:
  CREATE src/stores/auth.ts:
    - IMPLEMENT Pinia store for authentication state
    - HANDLE login/logout/register actions
    - MANAGE JWT token persistence in localStorage

  CREATE src/components/forms/LoginForm.vue:
    - BUILD reactive form with validation
    - CONNECT to auth store actions
    - HANDLE error states and loading indicators

Task 8 - Analysis Dashboard:
  CREATE src/stores/analysis.ts:
    - IMPLEMENT analysis data management
    - SETUP real-time subscriptions for status updates
    - HANDLE polling fallback for older browsers

  CREATE src/components/dashboard/ScoreGauge.vue:
    - BUILD Chart.js gauge component
    - MAKE responsive and accessible
    - FOLLOW Vue 3 composition API patterns

Task 9 - Analysis Form & Results:
  CREATE src/components/forms/AnalysisForm.vue:
    - IMPLEMENT URL input with validation
    - CONNECT to analysis submission API
    - SHOW immediate feedback on submission

  CREATE src/views/AnalysisView.vue:
    - DISPLAY comprehensive analysis results
    - IMPLEMENT data visualization components
    - HANDLE loading and error states

Task 10 - Docker & Deployment:
  CREATE docker-compose.yml:
    - DEFINE frontend, backend, worker, redis services
    - SETUP proper networking and volume mounts
    - CONFIGURE environment variable passing

  CREATE Dockerfile for backend and frontend:
    - OPTIMIZE for production builds
    - IMPLEMENT proper security practices
    - KEEP image sizes minimal
```

### Pseudocode for Critical Tasks

```python
# Task 5 - Celery Worker Implementation
@celery_app.task(bind=True, name='tasks.perform_seo_analysis')
def perform_seo_analysis(self, analysis_task_id: str, url: str):
    # PATTERN: Always update status first
    db_service = SupabaseService(supabase_admin)
    
    try:
        # CRITICAL: Update to IN_PROGRESS immediately
        db_service.update_analysis_task(
            task_id=analysis_task_id,
            updates={'status': 'IN_PROGRESS', 'celery_task_id': self.request.id}
        )
        
        # PATTERN: Use service layer abstraction
        seo_service = SeoAnalysisService()
        
        # GOTCHA: Wrap in timeout to prevent hanging
        with timeout(300):  # 5 minute timeout
            results = seo_service.analyze_website(url)
        
        # CRITICAL: Store results atomically
        db_service.update_analysis_task(
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
        
        db_service.update_analysis_task(
            task_id=analysis_task_id,
            updates={
                'status': 'FAILED',
                'error_message': str(e),
                'completed_at': datetime.utcnow().isoformat()
            }
        )
        
        # CRITICAL: Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries), max_retries=3)

# Task 8 - Real-time Updates
def subscribeToUpdates(userId: string) {
    // PATTERN: Use specific channel naming
    subscription = supabase
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
                    showNotification('Analysis completed!', 'success')
                }
            }
        )
        .subscribe()
}
```

### Integration Points

```yaml
SUPABASE:
  - configuration: "Set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"
  - migrations: "Run SQL files in migrations/ directory on Supabase"
  - RLS: "Enable Row Level Security on all user data tables"

CELERY:
  - broker: "Configure Redis URL for task queue"
  - monitoring: "Use Flower for task monitoring in development"
  - scaling: "Scale workers horizontally based on queue depth"

FRONTEND:
  - api: "Configure VITE_API_URL to point to FastAPI backend"
  - supabase: "Configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY"
  - routing: "Setup Vue Router with authentication guards"

AUTHENTICATION:
  - tokens: "JWT tokens passed in Authorization: Bearer headers"
  - refresh: "Implement automatic token refresh before expiration"
  - logout: "Clear tokens from localStorage and Supabase session"
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
# CREATE test files for each service/component

# Backend - test_supabase_service.py
def test_create_analysis_task():
    """Test creating analysis task creates record with correct data"""
    service = SupabaseService(mock_client)
    task_data = AnalysisTaskCreate(url="https://example.com")
    
    result = service.create_analysis_task("user-123", task_data)
    
    assert result['url_analyzed'] == "https://example.com"
    assert result['status'] == 'PENDING'
    assert result['user_id'] == "user-123"

def test_update_analysis_task():
    """Test updating task status works correctly"""
    service = SupabaseService(mock_client)
    
    result = service.update_analysis_task(
        "task-123", 
        {"status": "SUCCESS", "results": {"score": 85}}
    )
    
    assert result['status'] == 'SUCCESS'
    assert result['results']['score'] == 85

# Frontend - stores/auth.test.ts
describe('Auth Store', () => {
  it('should login successfully and store user data', async () => {
    const authStore = useAuthStore()
    
    await authStore.login({
      email: 'test@example.com',
      password: 'password123'
    })
    
    expect(authStore.isAuthenticated).toBe(true)
    expect(authStore.user?.email).toBe('test@example.com')
  })
  
  it('should handle login errors gracefully', async () => {
    const authStore = useAuthStore()
    
    await expect(authStore.login({
      email: 'invalid@example.com',
      password: 'wrongpassword'
    })).rejects.toThrow()
    
    expect(authStore.isAuthenticated).toBe(false)
  })
})
```

```bash
# Run and iterate until passing
cd backend && python -m pytest tests/ -v --cov=app
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
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "full_name": "Test User"}'

# Expected: 201 Created with user object

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Expected: 200 OK with access_token

# Test analysis submission (replace TOKEN with actual token from login)
curl -X POST http://localhost:8000/api/v1/analyses/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"url": "https://example.com"}'

# Expected: 202 Accepted with task_id

# Test frontend loads
curl -I http://localhost:3000
# Expected: 200 OK

# Check logs for errors
docker-compose logs backend | grep ERROR
docker-compose logs worker | grep ERROR

# If errors: Check application logs, fix issues, restart services
```

## Final Validation Checklist

- [ ] All unit tests pass: `cd backend && python -m pytest tests/ -v`
- [ ] All frontend tests pass: `cd frontend && npm run test:unit`
- [ ] No linting errors: `ruff check backend/app/` and `npm run lint` in frontend
- [ ] No type errors: `mypy backend/app/` and `npm run type-check` in frontend
- [ ] Docker services start successfully: `docker-compose up -d`
- [ ] User registration/login works via API
- [ ] Analysis submission returns task_id immediately
- [ ] Frontend dashboard loads and displays data
- [ ] Real-time updates work when analysis completes
- [ ] Error cases return proper HTTP status codes and messages
- [ ] Database has proper RLS policies enabled
- [ ] All environment variables are documented in .env.example

---

## Anti-Patterns to Avoid

- ❌ **Don't use sync database calls in async FastAPI endpoints** - causes blocking
- ❌ **Don't skip Row Level Security policies** - creates security vulnerabilities  
- ❌ **Don't pass complex objects to Celery tasks** - causes serialization errors
- ❌ **Don't forget .value when updating Vue refs** - breaks reactivity
- ❌ **Don't hardcode Supabase credentials** - use environment variables
- ❌ **Don't ignore Celery task failures** - implement proper retry logic
- ❌ **Don't mix authentication methods** - choose Supabase Auth OR custom JWT, not both
- ❌ **Don't skip input validation** - validate all user inputs with Pydantic
- ❌ **Don't block the main thread** - use background tasks for long-running operations
- ❌ **Don't assume network requests succeed** - wrap in try/catch with timeouts

**Critical Success Factor**: Follow the validation loops strictly. Each level must pass before proceeding to the next. This ensures working code at every step.