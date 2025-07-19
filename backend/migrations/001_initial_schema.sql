-- Migration: 001_initial_schema.sql
-- Description: Initial schema for Core Website Vitals SaaS platform
-- Created: 2025-01-17
-- This migration sets up the core tables and RLS policies for multi-tenant security

-- Create profiles table (extends auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    subscription_tier VARCHAR(50) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'business', 'enterprise')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analysis_tasks table for tracking SEO analysis jobs
CREATE TABLE public.analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    url_analyzed VARCHAR(2048) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'CANCELLED')),
    celery_task_id VARCHAR(255) UNIQUE,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    error_message TEXT,
    analysis_type VARCHAR(50) DEFAULT 'full_seo' CHECK (analysis_type IN ('full_seo', 'quick_scan', 'technical_only', 'content_only')),
    
    -- Constraints
    CONSTRAINT valid_timestamps CHECK (
        (started_at IS NULL OR started_at >= submitted_at) AND
        (completed_at IS NULL OR completed_at >= COALESCE(started_at, submitted_at))
    ),
    CONSTRAINT valid_status_transition CHECK (
        (status = 'PENDING' AND started_at IS NULL AND completed_at IS NULL) OR
        (status = 'IN_PROGRESS' AND started_at IS NOT NULL AND completed_at IS NULL) OR
        (status IN ('SUCCESS', 'FAILED', 'CANCELLED') AND completed_at IS NOT NULL)
    )
);

-- Create indexes for performance optimization
CREATE INDEX idx_profiles_email ON public.profiles(email);
CREATE INDEX idx_profiles_subscription_tier ON public.profiles(subscription_tier);
CREATE INDEX idx_analysis_tasks_user_id_submitted_at ON public.analysis_tasks(user_id, submitted_at DESC);
CREATE INDEX idx_analysis_tasks_status ON public.analysis_tasks(status);
CREATE INDEX idx_analysis_tasks_celery_task_id ON public.analysis_tasks(celery_task_id);
CREATE INDEX idx_analysis_tasks_created_at ON public.analysis_tasks(submitted_at DESC);
CREATE INDEX idx_analysis_tasks_url_analyzed ON public.analysis_tasks(url_analyzed);

-- Enable Row Level Security for multi-tenant isolation
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles table
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE 
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON public.profiles
    FOR INSERT 
    WITH CHECK (auth.uid() = id);

-- RLS Policies for analysis_tasks table
CREATE POLICY "Users can view their own analysis tasks" ON public.analysis_tasks
    FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own analysis tasks" ON public.analysis_tasks
    FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analysis tasks" ON public.analysis_tasks
    FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analysis tasks" ON public.analysis_tasks
    FOR DELETE 
    USING (auth.uid() = user_id);

-- Service role policies for backend operations
CREATE POLICY "Service role can manage all profiles" ON public.profiles
    FOR ALL 
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage all analysis tasks" ON public.analysis_tasks
    FOR ALL 
    USING (auth.role() = 'service_role');

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for profiles table
CREATE TRIGGER update_profiles_updated_at 
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW 
    EXECUTE FUNCTION public.update_updated_at_column();

-- Create function to handle user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ language 'plpgsql' SECURITY DEFINER;

-- Create trigger for automatic profile creation
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Create view for dashboard analytics (with RLS)
CREATE VIEW public.user_analysis_summary AS
SELECT 
    user_id,
    COUNT(*) as total_analyses,
    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_analyses,
    COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed_analyses,
    COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending_analyses,
    COUNT(CASE WHEN status = 'IN_PROGRESS' THEN 1 END) as in_progress_analyses,
    MAX(submitted_at) as last_analysis_date,
    AVG(EXTRACT(EPOCH FROM (completed_at - submitted_at))) as avg_analysis_time_seconds
FROM public.analysis_tasks
WHERE completed_at IS NOT NULL
GROUP BY user_id;

-- Enable RLS on the view
ALTER VIEW public.user_analysis_summary SET (security_invoker = true);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated, service_role;
GRANT ALL ON public.profiles TO authenticated, service_role;
GRANT ALL ON public.analysis_tasks TO authenticated, service_role;
GRANT SELECT ON public.user_analysis_summary TO authenticated, service_role;

-- Create subscription for real-time updates
-- This will be handled by the application layer using Supabase real-time features

-- Add comments for documentation
COMMENT ON TABLE public.profiles IS 'User profile information extending auth.users';
COMMENT ON TABLE public.analysis_tasks IS 'SEO analysis tasks with status tracking';
COMMENT ON COLUMN public.analysis_tasks.results IS 'JSONB column storing complete SEO analysis results';
COMMENT ON COLUMN public.analysis_tasks.celery_task_id IS 'Reference to Celery task for status tracking';
COMMENT ON VIEW public.user_analysis_summary IS 'Aggregated analysis statistics per user';

-- Migration completed successfully
-- Next steps: Run this migration in your Supabase dashboard SQL editor