---
inclusion: always
---

# Core Website Vitals Project Overview

## Project Description
Core Website Vitals is a SaaS platform that transforms the command-line python-seo-analyzer tool into a user-friendly web application. The platform enables users to perform SEO analysis through an intuitive dashboard, track historical performance, and receive actionable insights.

## Key Transformation
- **From**: Command-line Python utility for technical users
- **To**: Multi-tenant web application serving digital marketers, developers, and SEO professionals
- **Value**: Democratizes advanced SEO analysis with superior UX and real-time features

## Technology Stack
- **Frontend**: Vue.js 3 + TypeScript + Vite (Composition API, Pinia state management)
- **Backend API**: FastAPI + Python 3.11+ (Async-first, auto-generated docs)
- **Database**: Supabase (PostgreSQL) with Row Level Security (RLS)
- **Task Queue**: Celery + Redis for background processing
- **Authentication**: Supabase Auth + JWT
- **Email Service**: Resend for email notifications
- **Deployment**: Docker + Docker Compose

## Architecture Overview
The system follows a modern microservices architecture with clear separation between frontend, backend, and worker components:

1. Vue.js SPA frontend for user interface
2. FastAPI backend for API endpoints and business logic
3. Supabase (PostgreSQL) for data storage with RLS for multi-tenant isolation
4. Redis-backed Celery queue for asynchronous task processing
5. Celery workers for executing SEO analysis tasks
6. Celery Beat for scheduled analysis tasks
7. Resend for email notifications about completed analyses and significant changes