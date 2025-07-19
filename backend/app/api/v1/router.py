"""
Main API router for Core Website Vitals v1 API.
Combines all endpoint routers into a single router.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, analyses, dashboard, users, websocket, trial

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    analyses.router,
    prefix="/analyses",
    tags=["SEO Analysis"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["User Management"]
)

api_router.include_router(
    websocket.router,
    prefix="/websocket",
    tags=["WebSocket"]
)

api_router.include_router(
    trial.router,
    prefix="/analyses",
    tags=["Trial Analysis"]
)