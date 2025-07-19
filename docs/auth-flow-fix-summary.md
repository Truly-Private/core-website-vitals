# Authentication Flow Fix Summary

## Root Cause Analysis

The authentication was failing because of a mismatch between frontend and backend auth systems:

1. **Frontend**: Was using Supabase Auth directly (Supabase JWT tokens)
2. **Backend**: Expected its own JWT tokens from `/api/v1/auth/*` endpoints

This caused a cascade of issues:
- Frontend sent Supabase tokens to backend
- Backend rejected these tokens (401 Unauthorized)
- Token refresh attempts hit Supabase instead of backend
- Multiple concurrent 401s caused rate limiting (429) on Supabase

## Solution Implemented

### 1. Refactored Auth Store (`/frontend/src/stores/auth.ts`)

**Changed authentication flow from Supabase to Backend API:**

#### Login
```typescript
// Before: Using Supabase directly
const { data, error } = await supabase.auth.signInWithPassword({
  email: credentials.email,
  password: credentials.password,
})

// After: Using backend API
const response = await apiClient.post('/auth/login', {
  email: credentials.email,
  password: credentials.password,
})
```

#### Registration
```typescript
// Before: Supabase signup + manual profile creation
const { data, error } = await supabase.auth.signUp({...})

// After: Backend handles everything
const response = await apiClient.post('/auth/register', {
  email: credentials.email,
  password: credentials.password,
  full_name: credentials.fullName,
})
```

#### Token Refresh
```typescript
// Before: Supabase session refresh
const { data, error } = await supabase.auth.refreshSession()

// After: Backend token refresh
const response = await apiClient.post('/auth/refresh', {
  refresh_token: refreshToken.value,
})
```

### 2. Removed Supabase Auth Dependencies

- Removed `supabase.auth.getSession()` from initialization
- Removed `supabase.auth.onAuthStateChange` listener
- Removed all Supabase auth event handling

### 3. JWT Token Handling

The backend returns JWT tokens that contain user info:
```typescript
// Decode JWT to get user info
const payload = JSON.parse(atob(access_token.split('.')[1]))
user.value = {
  id: payload.sub,
  email: payload.email,
  user_metadata: {
    full_name: payload.full_name,
  },
}
```

## Authentication Flow Now

1. **Login/Register**:
   - User submits credentials
   - Frontend calls backend `/auth/login` or `/auth/register`
   - Backend authenticates with Supabase internally
   - Backend generates its own JWT tokens
   - Frontend stores these tokens

2. **API Requests**:
   - Frontend sends backend JWT in Authorization header
   - Backend validates its own JWT
   - No more token mismatch

3. **Token Refresh**:
   - When backend JWT expires, frontend calls `/auth/refresh`
   - Backend issues new JWT pair
   - No more Supabase rate limiting

## Benefits

1. **Single Auth Flow**: All auth goes through backend
2. **No Token Mismatch**: Backend validates its own tokens
3. **No Rate Limiting**: Refresh handled by backend, not hitting Supabase directly
4. **Better Security**: Backend controls auth flow and token generation

## Testing

After these changes:
1. Clear browser storage: `localStorage.clear()`
2. Login should work without 401 errors
3. Profile should load correctly
4. No more 429 rate limit errors
5. Token refresh handled seamlessly

## Next Steps

1. Ensure backend has proper Supabase service role key configured
2. Monitor for any edge cases in token expiration
3. Consider implementing proactive token refresh before expiration