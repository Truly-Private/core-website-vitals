-- Remove foreign key constraint on user_id to allow trial analyses
ALTER TABLE public.analysis_tasks 
DROP CONSTRAINT IF EXISTS analysis_tasks_user_id_fkey;

-- Add a partial foreign key constraint that only applies to non-trial analyses
-- This allows trial analyses to have a user_id that doesn't exist in auth.users
CREATE OR REPLACE FUNCTION check_user_id_for_non_trial()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check foreign key for non-trial analyses
    IF NEW.is_trial = false AND NOT EXISTS (
        SELECT 1 FROM auth.users WHERE id = NEW.user_id
    ) THEN
        RAISE EXCEPTION 'user_id must exist in auth.users for non-trial analyses';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce the constraint
DROP TRIGGER IF EXISTS enforce_user_id_for_non_trial ON public.analysis_tasks;
CREATE TRIGGER enforce_user_id_for_non_trial
    BEFORE INSERT OR UPDATE ON public.analysis_tasks
    FOR EACH ROW
    EXECUTE FUNCTION check_user_id_for_non_trial();

-- Add comment explaining the approach
COMMENT ON COLUMN public.analysis_tasks.user_id IS 'User ID from auth.users for authenticated analyses, or generated UUID for trial analyses';