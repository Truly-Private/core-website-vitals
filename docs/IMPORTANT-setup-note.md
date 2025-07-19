# IMPORTANT: Supabase Service Role Key Setup

## Current Issue
The registration is failing because the `SUPABASE_SERVICE_ROLE_KEY` in the backend `.env` file is using a demo/placeholder key.

## How to Fix

1. **Get the real Service Role Key from Supabase**:
   - Go to your Supabase project dashboard
   - Navigate to Settings > API
   - Copy the "service_role" key (NOT the anon key)
   - This key starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` and is much longer

2. **Update the backend .env file**:
   ```bash
   cd backend
   # Edit .env and replace the SUPABASE_SERVICE_ROLE_KEY value
   ```

3. **SECURITY WARNING**: 
   - The service role key bypasses Row Level Security
   - NEVER commit this key to version control
   - NEVER expose it in client-side code
   - Only use it in backend services

## Why This is Needed
The service role key is required for:
- Creating user profiles after authentication
- Performing admin operations
- Bypassing RLS for system operations

## Email Configuration
The email service is already configured but disabled for development:
- `ENABLE_EMAIL_NOTIFICATIONS=False` - Emails will be logged instead of sent
- To enable real email sending:
  1. Get a Resend API key from resend.com
  2. Update `RESEND_API_KEY` in .env
  3. Set `ENABLE_EMAIL_NOTIFICATIONS=True`

## Testing
After updating the service role key, test registration with:
```bash
cd backend
python test_registration.py
```

The registration should succeed and you'll see logs about the welcome email (either sent or logged depending on your email configuration).