-- Add trial support columns to analysis_tasks table
ALTER TABLE public.analysis_tasks 
ADD COLUMN IF NOT EXISTS is_trial BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS trial_ip VARCHAR(45);

-- Create index for trial lookups
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_trial_ip ON public.analysis_tasks(trial_ip);
CREATE INDEX IF NOT EXISTS idx_analysis_tasks_is_trial ON public.analysis_tasks(is_trial);

-- Update RLS policy to allow reading trial analyses without authentication
CREATE POLICY "Trial analyses are viewable by anyone" 
ON public.analysis_tasks 
FOR SELECT 
USING (is_trial = true);

-- Allow inserting trial analyses without authentication
CREATE POLICY "Anyone can create trial analyses" 
ON public.analysis_tasks 
FOR INSERT 
WITH CHECK (is_trial = true);