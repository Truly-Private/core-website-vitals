# Migration Instructions for Trial Feature

The trial analysis feature requires additional columns in the `analysis_tasks` table. Follow these steps to apply the migration:

## Option 1: Via Supabase Dashboard (Recommended)

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the following SQL:

```sql
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
```

4. Click "Run" to execute the migration

## Option 2: Via Supabase CLI

If you have Supabase CLI installed:

```bash
supabase db push
```

## Option 3: For Local Development

If using local Supabase:

```bash
# Make sure Supabase is running
supabase start

# Apply migration
supabase db push --local
```

## After Migration

Once the migration is applied, update the trial endpoint code:

1. Edit `/backend/app/api/v1/endpoints/trial.py`
2. Uncomment the `is_trial` and `trial_ip` fields in the `task_data` dictionary (around line 91-92)

The trial feature will then work with proper tracking and rate limiting.