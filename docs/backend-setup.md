# Backend Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Copy `.env.example` to `.env` and update with your values:
   ```bash
   cp .env.example .env
   ```

   Key variables to configure:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_ANON_KEY`: Your Supabase anon key
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
   - `RESEND_API_KEY`: Your Resend API key for sending emails
   - `JWT_SECRET_KEY`: A secure random string for JWT signing

3. **Run the Development Server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Email Configuration

The backend uses two email systems:

### 1. Supabase Auth Emails
Supabase handles authentication emails (verification, password reset). These are configured in `supabase/config.toml` to use Resend SMTP.

### 2. Transactional Emails
The backend sends transactional emails (welcome, analysis complete) using Resend directly.

To enable email sending:
1. Sign up at [Resend.com](https://resend.com)
2. Create an API key
3. Add your domain and verify it
4. Set `RESEND_API_KEY` in your `.env` file
5. Set `ENABLE_EMAIL_NOTIFICATIONS=True`

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with:
```bash
pytest tests/ -v
```

## Docker Setup

If using Docker:
```bash
docker build -t core-website-vitals-backend .
docker run -p 8000:8000 --env-file .env core-website-vitals-backend
```

## Celery Worker

For background task processing:
```bash
celery -A app.worker.celery_app worker --loglevel=info
```

## Redis Setup

Redis is required for Celery. Install and run locally:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```