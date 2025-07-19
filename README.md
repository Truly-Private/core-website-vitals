# Core Website Vitals: SaaS SEO Analysis Platform 🚀

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Vue.js Version](https://img.shields.io/badge/vue.js-3.x-green.svg)](https://vuejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)

**Core Website Vitals** is a comprehensive SaaS platform that transforms the command-line python-seo-analyzer tool into a user-friendly web application. Built with Vue.js 3, FastAPI, and Supabase, it provides powerful SEO analysis capabilities with real-time updates, multi-tenant support, and enterprise-grade features.

## 🌟 Platform Overview

Core Website Vitals democratizes advanced SEO analysis by providing:

- **Full-Stack Web Application**: Modern Vue.js 3 frontend with FastAPI backend
- **Multi-Tenant SaaS Architecture**: Secure user authentication and data isolation
- **Real-Time Analysis**: Live updates and progress tracking
- **Comprehensive SEO Audits**: On-page, technical, content, and performance analysis
- **Historical Tracking**: Track SEO progress over time
- **Team Collaboration**: Share analyses and collaborate with team members
- **Export & Reporting**: Multiple export formats (PDF, CSV, JSON, HTML)

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Vue.js 3 + TypeScript + Vite | Modern reactive UI with type safety |
| **Backend** | FastAPI + Python 3.11+ | High-performance async API |
| **Database** | Supabase (PostgreSQL) | Managed database with RLS |
| **Authentication** | Supabase Auth + JWT | Secure user management |
| **Task Queue** | Celery + Redis | Background processing |
| **Deployment** | Docker + Docker Compose | Containerized deployment |

### System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Vue.js SPA    │───▶│     Nginx    │───▶│  FastAPI Server │
│   (Frontend)    │    │(Reverse Proxy)│    │   (Backend)     │
└─────────────────┘    └──────────────┘    └────────┬────────┘
         │                                           │
         │ WebSocket/HTTP                            │ SQL Queries
         ▼                                           ▼
┌─────────────────┐                        ┌─────────────────┐
│   Supabase DB   │                        │   Redis Cache   │
│(Users, Results) │                        │  (Task Queue)   │
└─────────────────┘                        └────────┬────────┘
                                                     │
                                                     │ Task Messages
                                                     ▼
                                            ┌─────────────────┐
                                            │  Celery Worker  │
                                            │ (SEO Analysis)  │
                                            └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/core-website-vitals.git
   cd core-website-vitals
   ```

2. **Environment Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Prerequisites Setup

1. **Install Supabase CLI:**
   ```bash
   npm install -g supabase
   ```

2. **Start local services:**
   ```bash
   # Start Redis (required for Celery)
   redis-server
   
   # Start Supabase local development
   supabase start
   ```

#### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment variables are already configured in the root `.env` file:**
   ```bash
   # The .env file contains both local and production configurations
   # For local development, it uses:
   # - LOCAL_SUPABASE_URL=http://127.0.0.1:54321
   # - LOCAL_SUPABASE_ANON_KEY=...
   # - DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
   ```

4. **Database migrations are already applied:**
   ```bash
   # The initial schema has been migrated to both local and remote Supabase
   # Tables created: profiles, analysis_tasks, notifications, analysis_history, user_settings
   ```

5. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Start Celery worker (in a separate terminal):**
   ```bash
   cd backend
   source venv/bin/activate  # Activate virtual environment
   celery -A app.worker.celery_app worker --loglevel=info
   ```

#### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Environment variables are configured in the root `.env` file:**
   ```bash
   # Frontend uses these variables from the root .env:
   # VITE_API_BASE_URL=http://localhost:8000/api/v1
   # VITE_SUPABASE_URL=http://127.0.0.1:54321
   # VITE_SUPABASE_ANON_KEY=...
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

#### Access Your Application

Once all services are running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Supabase Studio**: http://127.0.0.1:54323
- **Mailpit (Email Testing)**: http://127.0.0.1:54324

#### Development Workflow

1. **Start all services in this order:**
   ```bash
   # Terminal 1: Start Redis
   redis-server
   
   # Terminal 2: Start Supabase
   supabase start
   
   # Terminal 3: Start Backend
   cd backend && source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 4: Start Celery Worker
   cd backend && source venv/bin/activate
   celery -A app.worker.celery_app worker --loglevel=info
   
   # Terminal 5: Start Frontend
   cd frontend
   npm run dev
   ```

2. **Check service health:**
   ```bash
   # Check Supabase status
   supabase status
   
   # Check Redis connection
   redis-cli ping
   
   # Check backend API
   curl http://localhost:8000/health
   ```

### Development Commands

#### Backend Commands
```bash
cd backend

# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Start API server

# Background processing
celery -A app.worker.celery_app worker --loglevel=info     # Start worker
celery -A app.worker.celery_app beat --loglevel=info       # Start scheduler (optional)

# Database operations
supabase migration new <migration_name>                    # Create new migration
supabase db push                                           # Push schema changes
supabase db pull                                           # Pull schema changes
supabase db reset                                          # Reset local database

# Testing
python -m pytest tests/ -v                                 # Run tests
python -m pytest tests/ -v --cov=app                       # Run tests with coverage
python -m pytest tests/unit/ -v                            # Run unit tests only
python -m pytest tests/integration/ -v                     # Run integration tests only

# Code quality
black .                                                     # Format code
isort .                                                     # Sort imports
flake8 .                                                   # Lint code
mypy .                                                     # Type checking
```

#### Frontend Commands
```bash
cd frontend

# Development
npm run dev          # Start development server (http://localhost:3000)
npm run build        # Build for production
npm run preview      # Preview production build
npm run serve        # Serve production build

# Testing
npm run test:unit    # Run unit tests
npm run test:e2e     # Run end-to-end tests
npm run test:coverage # Run tests with coverage

# Code quality
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint issues
npm run type-check   # Run TypeScript type checking
npm run format       # Format code with Prettier

# Dependencies
npm run update       # Update dependencies
npm audit            # Check for vulnerabilities
```

#### Project-Wide Commands
```bash
# Start all services for development
npm run dev:all      # Start all services concurrently (if script exists)

# Database management
supabase start       # Start local Supabase
supabase stop        # Stop local Supabase  
supabase status      # Check service status
supabase logs        # View logs

# Docker operations
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose logs -f                  # View logs
docker-compose exec backend bash       # Access backend container
docker-compose exec frontend sh        # Access frontend container
```

## 🔧 Configuration

### Environment Variables

The project uses a single `.env` file in the root directory that configures both frontend and backend services. Here are the key sections:

**Supabase Configuration:**
```env
# Production (Remote Supabase)
SUPABASE_URL=https://kermpzcdqlgltgwicspi.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Local Development (Local Supabase)
LOCAL_SUPABASE_URL=http://127.0.0.1:54321
LOCAL_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
LOCAL_SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Backend Configuration:**
```env
# Database and Authentication
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
JWT_SECRET_KEY=super-secret-jwt-token-with-at-least-32-characters-long

# Task Queue and Caching
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Configuration
API_HOST=localhost
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://corewebsitevitals.com
```

**Frontend Configuration:**
```env
# API and Services
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Development Settings
NODE_ENV=development
DEBUG=true
```

### Database Setup

The database is automatically configured and migrated:

1. **Supabase Project**: Already created (`kermpzcdqlgltgwicspi`)
2. **Schema Migration**: Applied via `supabase/migrations/001_initial_schema.sql`
3. **Tables Created**:
   - `profiles` - User profiles with subscription management
   - `analysis_tasks` - SEO analysis tasks and results
   - `notifications` - User notification system
   - `analysis_history` - Audit log for analysis changes
   - `user_settings` - User preferences and configuration

4. **Security Features**:
   - Row Level Security (RLS) enabled on all tables
   - Automatic user profile creation on registration
   - Service role policies for backend operations
   - Comprehensive indexes for performance

5. **Local Development**: 
   - Local Supabase instance handles all database operations
   - Same schema as production for consistency
   - Real-time subscriptions for live updates

## 📊 SEO Analysis Features

### Comprehensive Analysis Types

1. **Full SEO Analysis**: Complete audit including all aspects
2. **Technical SEO**: Focus on technical implementation
3. **Content Analysis**: Content quality and keyword optimization
4. **Performance Audit**: Core Web Vitals and performance metrics

### Analysis Capabilities

- **On-Page SEO**: Meta tags, headings, images, links, content quality
- **Technical SEO**: Core Web Vitals, crawlability, security, structured data
- **Content Analysis**: Keyword density, readability, text-to-HTML ratio
- **Performance Metrics**: Loading speed, LCP, FID, CLS
- **Security Checks**: SSL, HTTPS, mixed content detection
- **Mobile Optimization**: Responsive design, viewport configuration

### Key Features

- **Real-Time Updates**: Live progress tracking during analysis
- **Batch Processing**: Analyze multiple URLs simultaneously
- **Historical Tracking**: Track SEO improvements over time
- **Custom Scoring**: Configurable scoring weights and criteria
- **Export Options**: PDF reports, CSV data, JSON exports
- **Team Collaboration**: Share analyses with team members

## 🛠️ API Documentation

### Authentication

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "full_name": "John Doe"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Analysis API

```bash
# Submit new analysis
curl -X POST http://localhost:8000/api/v1/analyses/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "analysis_type": "full_seo"}'

# Get analysis results
curl -X GET http://localhost:8000/api/v1/analyses/{analysis_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm run test:unit
npm run test:e2e
```

## 📦 Deployment

### Production Docker Setup

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

### Environment-Specific Configurations

- **Development**: Local development with hot reloading
- **Staging**: Pre-production testing environment
- **Production**: Optimized build with security hardening

## 🔒 Security

- **Row Level Security (RLS)**: Database-level access control
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive input sanitization
- **CORS Configuration**: Secure cross-origin resource sharing
- **Rate Limiting**: API rate limiting to prevent abuse

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built upon the excellent work of the original [python-seo-analyzer](https://github.com/ihuzaifashoukat/seo-analyzer) created by [ihuzaifashoukat](https://github.com/ihuzaifashoukat). We extend our gratitude for providing the foundation SEO analysis modules that power this SaaS platform.

### Original Project

- **Repository**: https://github.com/ihuzaifashoukat/seo-analyzer
- **Author**: [ihuzaifashoukat](https://github.com/ihuzaifashoukat)
- **License**: MIT

The original command-line tool provided the core SEO analysis capabilities that have been integrated into this full-stack SaaS platform. We encourage users to also check out the original project for command-line usage.

### Support the Original Author

If you find the underlying SEO analysis capabilities useful, consider supporting the original author:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/ihuzaifashoukat)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/core-website-vitals/issues)
- **Documentation**: [Wiki](https://github.com/your-username/core-website-vitals/wiki)
- **Email**: support@corewebsitevitals.com

---

*Transform your SEO analysis workflow with Core Website Vitals - the modern SaaS platform for comprehensive website optimization.*