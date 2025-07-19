-- Core Website Vitals - Initial Database Schema
-- This migration sets up the initial database structure for the SaaS platform

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create custom types
CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'business', 'enterprise');
CREATE TYPE analysis_status AS ENUM ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'CANCELLED');
CREATE TYPE analysis_type AS ENUM ('full_seo', 'technical_seo', 'content_analysis', 'performance_audit');

-- Create profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    subscription_tier subscription_tier DEFAULT 'free',
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analysis_tasks table
CREATE TABLE IF NOT EXISTS public.analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    url_analyzed VARCHAR(2048) NOT NULL,
    analysis_type analysis_type NOT NULL DEFAULT 'full_seo',
    status analysis_status NOT NULL DEFAULT 'PENDING',
    celery_task_id VARCHAR(255) UNIQUE,
    
    -- Timestamps
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Analysis configuration
    target_keywords TEXT[],
    custom_options JSONB DEFAULT '{}',
    
    -- Results and progress
    results JSONB,
    progress_data JSONB,
    error_message TEXT,
    
    -- Metadata
    user_agent VARCHAR(500),
    ip_address INET,
    
    -- Indexes for performance
    CONSTRAINT valid_url CHECK (url_analyzed ~ '^https?://'),
    CONSTRAINT valid_status_transitions CHECK (
        (status = 'PENDING' AND started_at IS NULL) OR
        (status = 'IN_PROGRESS' AND started_at IS NOT NULL) OR
        (status IN ('SUCCESS', 'FAILED', 'CANCELLED') AND completed_at IS NOT NULL)
    )
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Notification metadata
    related_analysis_id UUID REFERENCES public.analysis_tasks(id) ON DELETE CASCADE,
    action_url VARCHAR(500),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create analysis_history table for tracking changes
CREATE TABLE IF NOT EXISTS public.analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_task_id UUID REFERENCES public.analysis_tasks(id) ON DELETE CASCADE NOT NULL,
    old_status analysis_status,
    new_status analysis_status NOT NULL,
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Create user_settings table
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    
    -- Notification preferences
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    analysis_complete_notifications BOOLEAN DEFAULT TRUE,
    weekly_report_notifications BOOLEAN DEFAULT TRUE,
    
    -- UI preferences
    theme VARCHAR(20) DEFAULT 'system',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Analysis preferences
    default_analysis_type analysis_type DEFAULT 'full_seo',
    auto_retry_failed_analyses BOOLEAN DEFAULT TRUE,
    max_concurrent_analyses INTEGER DEFAULT 5,
    
    -- Other settings
    settings_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_subscription_tier ON public.profiles(subscription_tier);

CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id ON public.analysis_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON public.analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_submitted_at ON public.analysis_tasks(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_id_submitted_at ON public.analysis_tasks(user_id, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_celery_task_id ON public.analysis_tasks(celery_task_id);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_url_analyzed ON public.analysis_tasks(url_analyzed);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON public.notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_read_at ON public.notifications(read_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id_created_at ON public.notifications(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_history_analysis_task_id ON public.analysis_history(analysis_task_id);
CREATE INDEX IF NOT EXISTS idx_analysis_history_changed_at ON public.analysis_history(changed_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER handle_updated_at_profiles
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER handle_updated_at_user_settings
    BEFORE UPDATE ON public.user_settings
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- Create function to automatically create user profile and settings
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    
    INSERT INTO public.user_settings (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user registration
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Create function to track analysis status changes
CREATE OR REPLACE FUNCTION public.track_analysis_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO public.analysis_history (analysis_task_id, old_status, new_status)
        VALUES (NEW.id, OLD.status, NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for analysis status changes
CREATE TRIGGER track_analysis_status_changes
    AFTER UPDATE ON public.analysis_tasks
    FOR EACH ROW
    EXECUTE FUNCTION public.track_analysis_status_change();

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for profiles
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Create RLS policies for analysis_tasks
CREATE POLICY "Users can view own analysis tasks" ON public.analysis_tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analysis tasks" ON public.analysis_tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own analysis tasks" ON public.analysis_tasks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own analysis tasks" ON public.analysis_tasks
    FOR DELETE USING (auth.uid() = user_id);

-- Create RLS policies for notifications
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- Create RLS policies for analysis_history
CREATE POLICY "Users can view own analysis history" ON public.analysis_history
    FOR SELECT USING (
        auth.uid() = (
            SELECT user_id FROM public.analysis_tasks 
            WHERE id = analysis_task_id
        )
    );

-- Create RLS policies for user_settings
CREATE POLICY "Users can view own settings" ON public.user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON public.user_settings
    FOR UPDATE USING (auth.uid() = user_id);

-- Create service role policies (for backend operations)
CREATE POLICY "Service role can manage all data" ON public.profiles
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage all analysis tasks" ON public.analysis_tasks
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage all notifications" ON public.notifications
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage all analysis history" ON public.analysis_history
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage all user settings" ON public.user_settings
    FOR ALL USING (auth.role() = 'service_role');

-- Create utility functions
CREATE OR REPLACE FUNCTION public.get_user_analysis_stats(user_uuid UUID)
RETURNS TABLE(
    total_analyses BIGINT,
    pending_analyses BIGINT,
    in_progress_analyses BIGINT,
    completed_analyses BIGINT,
    failed_analyses BIGINT,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_analyses,
        COUNT(*) FILTER (WHERE status = 'PENDING')::BIGINT as pending_analyses,
        COUNT(*) FILTER (WHERE status = 'IN_PROGRESS')::BIGINT as in_progress_analyses,
        COUNT(*) FILTER (WHERE status = 'SUCCESS')::BIGINT as completed_analyses,
        COUNT(*) FILTER (WHERE status = 'FAILED')::BIGINT as failed_analyses,
        CASE 
            WHEN COUNT(*) = 0 THEN 0
            ELSE ROUND(
                (COUNT(*) FILTER (WHERE status = 'SUCCESS')::NUMERIC / COUNT(*)::NUMERIC) * 100, 
                2
            )
        END as success_rate
    FROM public.analysis_tasks
    WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to clean up old completed analyses
CREATE OR REPLACE FUNCTION public.cleanup_old_analyses()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM public.analysis_tasks
    WHERE status IN ('SUCCESS', 'FAILED', 'CANCELLED')
    AND completed_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Insert default data
INSERT INTO public.profiles (id, email, full_name, subscription_tier)
SELECT 
    id,
    email,
    COALESCE(raw_user_meta_data->>'full_name', email),
    'free'
FROM auth.users
WHERE id NOT IN (SELECT id FROM public.profiles)
ON CONFLICT (id) DO NOTHING;

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_user_status_date ON public.analysis_tasks(user_id, status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_celery_status ON public.analysis_tasks(celery_task_id, status) WHERE celery_task_id IS NOT NULL;

-- Create partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_active ON public.analysis_tasks(user_id, submitted_at DESC) 
WHERE status IN ('PENDING', 'IN_PROGRESS');

CREATE INDEX IF NOT EXISTS idx_notifications_unread ON public.notifications(user_id, created_at DESC) 
WHERE read_at IS NULL;

COMMENT ON TABLE public.profiles IS 'User profiles extending auth.users with additional information';
COMMENT ON TABLE public.analysis_tasks IS 'SEO analysis tasks with results and metadata';
COMMENT ON TABLE public.notifications IS 'User notifications for various events';
COMMENT ON TABLE public.analysis_history IS 'Audit log for analysis status changes';
COMMENT ON TABLE public.user_settings IS 'User preferences and configuration settings';