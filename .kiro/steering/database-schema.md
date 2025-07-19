---
inclusion: fileMatch
fileMatchPattern: '*.sql'
---

# Database Schema

## Supabase Tables

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

-- Scheduled analyses
CREATE TABLE public.scheduled_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    url VARCHAR(2048) NOT NULL,
    frequency VARCHAR(50) NOT NULL, -- DAILY, WEEKLY, MONTHLY
    next_run TIMESTAMP WITH TIME ZONE NOT NULL,
    last_run TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analysis history
CREATE TABLE public.analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_task_id UUID REFERENCES public.analysis_tasks(id),
    scheduled_analysis_id UUID REFERENCES public.scheduled_analyses(id),
    previous_score INTEGER,
    current_score INTEGER,
    score_change INTEGER,
    notification_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheduled_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for analysis_tasks
CREATE POLICY "Users can view own analysis tasks" ON public.analysis_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own analysis tasks" ON public.analysis_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own analysis tasks" ON public.analysis_tasks
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for scheduled_analyses
CREATE POLICY "Users can view own scheduled analyses" ON public.scheduled_analyses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own scheduled analyses" ON public.scheduled_analyses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scheduled analyses" ON public.scheduled_analyses
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own scheduled analyses" ON public.scheduled_analyses
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for analysis_history
CREATE POLICY "Users can view own analysis history" ON public.analysis_history
    FOR SELECT USING (
        auth.uid() IN (
            SELECT user_id FROM public.analysis_tasks WHERE id = analysis_task_id
            UNION
            SELECT user_id FROM public.scheduled_analyses WHERE id = scheduled_analysis_id
        )
    );

-- Indexes for performance
CREATE INDEX idx_analysis_tasks_user_id_submitted_at 
    ON public.analysis_tasks(user_id, submitted_at DESC);
CREATE INDEX idx_analysis_tasks_status 
    ON public.analysis_tasks(status);
CREATE INDEX idx_analysis_tasks_celery_task_id 
    ON public.analysis_tasks(celery_task_id);
CREATE INDEX idx_scheduled_analyses_user_id 
    ON public.scheduled_analyses(user_id);
CREATE INDEX idx_scheduled_analyses_next_run 
    ON public.scheduled_analyses(next_run);
CREATE INDEX idx_analysis_history_analysis_task_id 
    ON public.analysis_history(analysis_task_id);
CREATE INDEX idx_analysis_history_scheduled_analysis_id 
    ON public.analysis_history(scheduled_analysis_id);
```

## Data Models (Pydantic Schemas)

```python
# Authentication Models
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

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: str = "free"
    created_at: datetime
    updated_at: datetime

# Analysis Models
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

class AnalysisResultsResponse(BaseModel):
    overall_score: int
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    detailed_results: Dict[str, Any]

# Scheduled Analysis Models
class ScheduledAnalysisCreate(BaseModel):
    url: HttpUrl
    frequency: str  # DAILY, WEEKLY, MONTHLY
    start_date: Optional[datetime] = None

class ScheduledAnalysisResponse(BaseModel):
    id: UUID
    user_id: UUID
    url: str
    frequency: str
    next_run: datetime
    last_run: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
```