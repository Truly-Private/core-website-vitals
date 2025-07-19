from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, Any
from datetime import datetime, timedelta
from app.models.schemas import AnalysisTaskCreate, AnalysisTaskResponse, AnalysisType as AnalysisTypeEnum
from app.services.analysis_service import AnalysisService
from app.services.supabase_service import SupabaseService
from app.core.supabase import get_supabase_client, get_supabase_admin_client
from app.core.config import settings
from app.worker.tasks import perform_trial_analysis
import uuid
import redis
import json

router = APIRouter()

# Redis client for rate limiting
redis_client = redis.from_url(settings.REDIS_URL)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host

def check_trial_rate_limit(client_ip: str) -> bool:
    """Check if IP has exceeded trial rate limit"""
    key = f"trial_rate_limit:{client_ip}"
    current_count = redis_client.get(key)
    
    if current_count is None:
        # First request from this IP
        redis_client.setex(key, 3600, 1)  # 1 hour expiry
        return True
    
    count = int(current_count)
    # Higher limit for development
    max_requests = 10 if settings.DEBUG else 3
    if count >= max_requests:  # Max requests per hour per IP
        return False
    
    redis_client.incr(key)
    return True

def check_trial_usage(client_ip: str) -> bool:
    """Check if IP has already used trial"""
    key = f"trial_used:{client_ip}"
    return redis_client.get(key) is None

def mark_trial_used(client_ip: str, analysis_id: str):
    """Mark trial as used for this IP"""
    key = f"trial_used:{client_ip}"
    # Store for 30 days
    redis_client.setex(key, 30 * 24 * 3600, analysis_id)

@router.post("/trial", response_model=AnalysisTaskResponse)
async def submit_trial_analysis(
    analysis_data: AnalysisTaskCreate,
    request: Request,
    supabase_client=Depends(get_supabase_admin_client)  # Use admin client to bypass RLS
):
    """Submit a trial SEO analysis without authentication"""
    
    client_ip = get_client_ip(request)
    
    # Check rate limiting
    if not check_trial_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many trial requests. Please try again later."
        )
    
    # Check if trial already used (skip in debug mode)
    if not settings.DEBUG and not check_trial_usage(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trial analysis has already been used from this IP address."
        )
    
    try:
        # Create a trial user ID based on IP
        # Using a deterministic UUID based on IP for tracking purposes
        trial_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"trial_{client_ip}"))
        
        # Create analysis task in database
        task_data = {
            "id": str(uuid.uuid4()),
            "user_id": trial_user_id,
            "url_analyzed": str(analysis_data.url),
            "status": "PENDING",
            "analysis_type": AnalysisTypeEnum.FULL_SEO.value,
            "submitted_at": datetime.utcnow().isoformat(),
            "is_trial": True,
            "trial_ip": client_ip
        }
        
        # Store in Supabase
        result = supabase_client.table("analysis_tasks").insert(task_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create analysis task"
            )
        
        task = result.data[0]
        
        # Mark trial as used
        mark_trial_used(client_ip, task["id"])
        
        # Dispatch Celery task for trial analysis
        celery_task = perform_trial_analysis.delay(task["id"], str(analysis_data.url))
        
        # Update task with Celery ID
        supabase_client.table("analysis_tasks").update({
            "celery_task_id": celery_task.id
        }).eq("id", task["id"]).execute()
        
        return AnalysisTaskResponse(
            id=task["id"],
            user_id=task["user_id"],
            url_analyzed=task["url_analyzed"],
            status=task["status"],
            celery_task_id=celery_task.id,
            submitted_at=task["submitted_at"],
            analysis_type=task["analysis_type"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit analysis: {str(e)}"
        )

@router.get("/trial/{analysis_id}", response_model=AnalysisTaskResponse)
async def get_trial_analysis(
    analysis_id: str,
    request: Request,
    supabase_client=Depends(get_supabase_admin_client)  # Use admin client to bypass RLS
):
    """Get trial analysis results"""
    
    client_ip = get_client_ip(request)
    
    try:
        # Fetch analysis task
        result = supabase_client.table("analysis_tasks").select("*").eq("id", analysis_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        task = result.data[0]
        
        # Verify this is a trial analysis
        if not task.get("is_trial"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is not a trial analysis"
            )
        
        
        return AnalysisTaskResponse(
            id=task["id"],
            user_id=task["user_id"],
            url_analyzed=task["url_analyzed"],
            status=task["status"],
            celery_task_id=task.get("celery_task_id"),
            submitted_at=task["submitted_at"],
            completed_at=task.get("completed_at"),
            analysis_type=task["analysis_type"],
            results=task.get("results"),
            error_message=task.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analysis: {str(e)}"
        )