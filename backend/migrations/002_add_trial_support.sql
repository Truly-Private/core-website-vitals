-- Add trial support columns to analysis_tasks table
ALTER TABLE public.analysis_tasks
ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS trial_ip VARCHAR(255);

-- Create index for trial lookups
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_trial 
    ON public.analysis_tasks(is_trial, trial_ip) 
    WHERE is_trial = TRUE;

-- Create a function to automatically set completed_at for SUCCESS status
CREATE OR REPLACE FUNCTION update_analysis_completed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'SUCCESS' AND OLD.status != 'SUCCESS' THEN
        NEW.completed_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic completed_at update
DROP TRIGGER IF EXISTS trigger_update_analysis_completed_at ON public.analysis_tasks;
CREATE TRIGGER trigger_update_analysis_completed_at
    BEFORE UPDATE ON public.analysis_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_analysis_completed_at();

-- Allow public read access to trial analyses
CREATE POLICY "Anyone can view trial analyses" ON public.analysis_tasks
    FOR SELECT
    USING (is_trial = TRUE);

-- Comment on new columns
COMMENT ON COLUMN public.analysis_tasks.is_trial IS 'Indicates if this is a trial analysis (no auth required)';
COMMENT ON COLUMN public.analysis_tasks.trial_ip IS 'IP address used for trial analysis (for rate limiting)';