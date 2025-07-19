"""
Pydantic schemas for Core Website Vitals API.
Defines request/response models for all API endpoints.
"""

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums
class AnalysisStatus(str, Enum):
    """Analysis task status options."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisType(str, Enum):
    """Analysis type options."""
    FULL_SEO = "full_seo"
    QUICK_SCAN = "quick_scan"
    TECHNICAL_ONLY = "technical_only"
    CONTENT_ONLY = "content_only"


class SubscriptionTier(str, Enum):
    """User subscription tier options."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


# Authentication Schemas
class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    }


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }
    }


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# User Schemas
class UserResponse(BaseModel):
    """User response model."""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: SubscriptionTier
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "subscription_tier": "pro",
                "created_at": "2025-01-17T10:00:00Z",
                "updated_at": "2025-01-17T10:00:00Z"
            }
        }
    }


class UserUpdateRequest(BaseModel):
    """User update request."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "John Smith",
                "avatar_url": "https://example.com/new-avatar.jpg"
            }
        }
    }


class UserProfileResponse(BaseModel):
    """Detailed user profile response."""
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: SubscriptionTier
    created_at: datetime
    updated_at: datetime
    total_analyses: int
    successful_analyses: int
    failed_analyses: int
    last_analysis_date: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }


class UserSettingsResponse(BaseModel):
    """User settings response."""
    email_notifications: bool = True
    real_time_updates: bool = True
    analysis_notifications: bool = True
    weekly_reports: bool = False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email_notifications": True,
                "real_time_updates": True,
                "analysis_notifications": True,
                "weekly_reports": False
            }
        }
    }


class UserSettingsUpdateRequest(BaseModel):
    """User settings update request."""
    email_notifications: Optional[bool] = None
    real_time_updates: Optional[bool] = None
    analysis_notifications: Optional[bool] = None
    weekly_reports: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword123"
            }
        }
    }


# Analysis Schemas
class AnalysisTaskCreate(BaseModel):
    """Analysis task creation request."""
    url: HttpUrl
    analysis_type: AnalysisType = AnalysisType.FULL_SEO
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://example.com",
                "analysis_type": "full_seo"
            }
        }
    }


class AnalysisTaskResponse(BaseModel):
    """Analysis task response."""
    id: UUID
    user_id: UUID
    url_analyzed: str
    status: AnalysisStatus
    analysis_type: AnalysisType
    celery_task_id: Optional[str] = None
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    is_trial: Optional[bool] = None
    trial_ip: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "url_analyzed": "https://example.com",
                "status": "SUCCESS",
                "analysis_type": "full_seo",
                "celery_task_id": "abc123-def456-ghi789",
                "submitted_at": "2025-01-17T10:00:00Z",
                "started_at": "2025-01-17T10:00:30Z",
                "completed_at": "2025-01-17T10:02:15Z",
                "results": {
                    "overall_score": 85,
                    "seo_attributes": {}
                },
                "error_message": None
            }
        }
    }


class AnalysisTaskUpdate(BaseModel):
    """Analysis task update request."""
    status: Optional[AnalysisStatus] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "CANCELLED"
            }
        }
    }


class AnalysisTaskListResponse(BaseModel):
    """Paginated analysis task list response."""
    items: List[AnalysisTaskResponse]
    total: int
    page: int
    page_size: int
    pages: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 50,
                "page": 1,
                "page_size": 10,
                "pages": 5
            }
        }
    }


# Dashboard Schemas
class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response."""
    total_analyses: int
    successful_analyses: int
    failed_analyses: int
    pending_analyses: int
    average_score: float
    average_analysis_time: float
    last_analysis_date: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_analyses": 45,
                "successful_analyses": 42,
                "failed_analyses": 2,
                "pending_analyses": 1,
                "average_score": 78.5,
                "average_analysis_time": 125.3,
                "last_analysis_date": "2025-01-17T10:00:00Z"
            }
        }
    }


class TrendDataPoint(BaseModel):
    """Single trend data point."""
    date: datetime
    value: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2025-01-17T10:00:00Z",
                "value": 78.5
            }
        }
    }


class DashboardTrendsResponse(BaseModel):
    """Dashboard trends response."""
    metric: str
    data_points: List[TrendDataPoint]
    trend_direction: str  # "up", "down", "stable"
    trend_percentage: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "metric": "overall_score",
                "data_points": [],
                "trend_direction": "up",
                "trend_percentage": 5.2
            }
        }
    }


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response."""
    on_page_score: float
    technical_score: float
    content_score: float
    overall_score: float
    common_issues: List[str]
    top_performing_urls: List[str]
    analysis_frequency: Dict[str, int]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "on_page_score": 82.3,
                "technical_score": 78.1,
                "content_score": 75.6,
                "overall_score": 78.7,
                "common_issues": ["Title too short", "Missing meta description"],
                "top_performing_urls": ["https://example.com/page1", "https://example.com/page2"],
                "analysis_frequency": {"daily": 2, "weekly": 8, "monthly": 15}
            }
        }
    }


# SEO Result Schemas
class SEOScoreData(BaseModel):
    """SEO score data structure."""
    score_percent: float
    issues: List[str]
    successes: List[str]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "score_percent": 85.2,
                "issues": ["Title too short", "Missing meta description"],
                "successes": ["HTTPS enabled", "H1 tag present"]
            }
        }
    }


class SEOAnalysisResults(BaseModel):
    """Complete SEO analysis results."""
    analysis_timestamp: datetime
    target_url: str
    domain: str
    on_page_score: SEOScoreData
    technical_score: SEOScoreData
    content_score: SEOScoreData
    overall_score_percent: float
    seo_attributes: Dict[str, Any]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "analysis_timestamp": "2025-01-17T10:00:00Z",
                "target_url": "https://example.com",
                "domain": "example.com",
                "on_page_score": {
                    "score_percent": 82.5,
                    "issues": ["Title too short"],
                    "successes": ["H1 tag present"]
                },
                "technical_score": {
                    "score_percent": 88.0,
                    "issues": ["Missing structured data"],
                    "successes": ["HTTPS enabled"]
                },
                "content_score": {
                    "score_percent": 75.3,
                    "issues": ["Content too short"],
                    "successes": ["Good readability"]
                },
                "overall_score_percent": 81.9,
                "seo_attributes": {}
            }
        }
    }


# Error Schemas
class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Union[str, int, float]]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "type": "validation_error",
                    "message": "Request validation failed",
                    "status_code": 422,
                    "timestamp": 1705483200.0
                }
            }
        }
    }


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: float
    version: str
    environment: Dict[str, bool]
    services: Dict[str, str]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": 1705483200.0,
                "version": "1.0.0",
                "environment": {
                    "debug": False,
                    "testing": False,
                    "production": True
                },
                "services": {
                    "supabase": "healthy",
                    "redis": "healthy",
                    "celery": "healthy"
                }
            }
        }
    }