"""
Main FastAPI application for Core Website Vitals backend.
Handles app initialization, middleware, and routing.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog
import time
from typing import Dict, Any

from app.core.config import get_settings
from app.core.supabase import test_supabase_connection, close_supabase_connections
from app.api.v1.router import api_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive SaaS platform for SEO analysis and website optimization.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed information."""
    logger.warning(
        "Request validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "timestamp": time.time()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else "unknown",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "message": "Internal server error" if settings.is_production else str(exc),
                "timestamp": time.time()
            }
        }
    )


# Middleware configuration
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log all incoming requests and responses."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=round(process_time, 3),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Trusted host middleware (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring."""
    try:
        # Test Supabase connection
        supabase_healthy = test_supabase_connection()
        
        health_status = {
            "status": "healthy" if supabase_healthy else "unhealthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "environment": {
                "debug": settings.DEBUG,
                "testing": settings.TESTING,
                "production": settings.is_production
            },
            "services": {
                "supabase": "healthy" if supabase_healthy else "unhealthy",
                "redis": "unknown",  # Will be tested in Celery tasks
                "celery": "unknown"  # Will be tested in Celery tasks
            }
        }
        
        logger.info("Health check completed", status=health_status["status"])
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_url": "/health"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(
        "Application startup",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment="production" if settings.is_production else "development",
        debug=settings.DEBUG
    )
    
    # Test database connections
    if not test_supabase_connection():
        logger.error("Failed to connect to Supabase during startup")
        # In production, you might want to exit here
        # import sys; sys.exit(1)
    
    logger.info("Application startup completed successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Application shutdown initiated")
    
    # Close database connections
    close_supabase_connections()
    
    logger.info("Application shutdown completed")


# Export app instance for workers
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.BACKEND_RELOAD,
        log_level=settings.LOG_LEVEL
    )