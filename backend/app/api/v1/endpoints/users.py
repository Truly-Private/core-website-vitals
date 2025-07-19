"""
User management endpoints for Core Website Vitals API.
Handles user profile management and account settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_user_id
from app.core.supabase import get_cached_supabase_client
from app.services.auth_service import get_auth_service
from app.models.database import AnalysisTasksTable
from app.models.schemas import (
    UserResponse,
    UserUpdateRequest,
    UserProfileResponse,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
    ChangePasswordRequest,
    SubscriptionTier
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user information.
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        Current user profile data
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        user_data = await auth_service.get_current_user(current_user_id)
        return user_data
        
    except Exception as e:
        logger.error("Get current user endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update current user profile.
    
    Args:
        user_update: User update data
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated user profile
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        updated_user = await auth_service.update_user_profile(current_user_id, user_update)
        return updated_user
        
    except Exception as e:
        logger.error("Update current user endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete current user account.
    
    Args:
        current_user_id: Current authenticated user ID
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        await auth_service.delete_user_account(current_user_id)
        
    except Exception as e:
        logger.error("Delete current user endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed user profile information.
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        Detailed user profile data
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        # Get user data
        user_data = await auth_service.get_current_user(current_user_id)
        
        # Get analysis summary
        analysis_tasks = AnalysisTasksTable(supabase_client)
        analysis_summary = await analysis_tasks.get_user_analysis_summary(current_user_id)
        
        if not analysis_summary:
            analysis_summary = {
                "total_analyses": 0,
                "successful_analyses": 0,
                "failed_analyses": 0,
                "last_analysis_date": None
            }
        
        return UserProfileResponse(
            id=user_data.id,
            email=user_data.email,
            full_name=user_data.full_name,
            avatar_url=user_data.avatar_url,
            subscription_tier=user_data.subscription_tier,
            created_at=user_data.created_at,
            updated_at=user_data.updated_at,
            total_analyses=analysis_summary["total_analyses"],
            successful_analyses=analysis_summary["successful_analyses"],
            failed_analyses=analysis_summary["failed_analyses"],
            last_analysis_date=analysis_summary["last_analysis_date"]
        )
        
    except Exception as e:
        logger.error("Get user profile endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user account settings.
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        User settings data
    """
    try:
        # For now, return default settings
        # In a real implementation, this would be stored in database
        return UserSettingsResponse(
            email_notifications=True,
            real_time_updates=True,
            analysis_notifications=True,
            weekly_reports=False
        )
        
    except Exception as e:
        logger.error("Get user settings endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user settings"
        )


@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdateRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Update user account settings.
    
    Args:
        settings_update: Settings update data
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated settings data
    """
    try:
        # For now, return updated settings
        # In a real implementation, this would be stored in database
        current_settings = UserSettingsResponse(
            email_notifications=True,
            real_time_updates=True,
            analysis_notifications=True,
            weekly_reports=False
        )
        
        # Apply updates
        if settings_update.email_notifications is not None:
            current_settings.email_notifications = settings_update.email_notifications
        if settings_update.real_time_updates is not None:
            current_settings.real_time_updates = settings_update.real_time_updates
        if settings_update.analysis_notifications is not None:
            current_settings.analysis_notifications = settings_update.analysis_notifications
        if settings_update.weekly_reports is not None:
            current_settings.weekly_reports = settings_update.weekly_reports
        
        logger.info("User settings updated successfully", user_id=current_user_id)
        return current_settings
        
    except Exception as e:
        logger.error("Update user settings endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user settings"
        )


@router.get("/me/subscription")
async def get_user_subscription(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user subscription information.
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        User subscription data
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        user_data = await auth_service.get_current_user(current_user_id)
        
        # Return subscription info with tier limits
        tier_limits = {
            SubscriptionTier.FREE: {
                "max_analyses_per_month": 10,
                "max_concurrent_analyses": 1,
                "features": ["basic_seo_analysis", "email_support"]
            },
            SubscriptionTier.PRO: {
                "max_analyses_per_month": 100,
                "max_concurrent_analyses": 3,
                "features": ["full_seo_analysis", "historical_tracking", "priority_support"]
            },
            SubscriptionTier.BUSINESS: {
                "max_analyses_per_month": 500,
                "max_concurrent_analyses": 10,
                "features": ["full_seo_analysis", "historical_tracking", "api_access", "white_label"]
            },
            SubscriptionTier.ENTERPRISE: {
                "max_analyses_per_month": -1,  # Unlimited
                "max_concurrent_analyses": 50,
                "features": ["full_seo_analysis", "historical_tracking", "api_access", "white_label", "custom_integrations"]
            }
        }
        
        return {
            "subscription_tier": user_data.subscription_tier,
            "limits": tier_limits.get(user_data.subscription_tier, tier_limits[SubscriptionTier.FREE]),
            "billing_period": "monthly",
            "next_billing_date": None,
            "status": "active"
        }
        
    except Exception as e:
        logger.error("Get user subscription endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user subscription"
        )


@router.get("/me/usage")
async def get_user_usage(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user API usage statistics.
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        User usage statistics
    """
    try:
        supabase_client = get_cached_supabase_client()
        analysis_tasks = AnalysisTasksTable(supabase_client)
        
        # Get analysis summary
        analysis_summary = await analysis_tasks.get_user_analysis_summary(current_user_id)
        
        if not analysis_summary:
            analysis_summary = {
                "total_analyses": 0,
                "successful_analyses": 0,
                "failed_analyses": 0,
                "pending_analyses": 0,
                "last_analysis_date": None
            }
        
        # Get current month analysis count
        # This would be a more complex query in a real implementation
        current_month_analyses = analysis_summary["total_analyses"]
        
        return {
            "current_month_analyses": current_month_analyses,
            "total_analyses": analysis_summary["total_analyses"],
            "successful_analyses": analysis_summary["successful_analyses"],
            "failed_analyses": analysis_summary["failed_analyses"],
            "pending_analyses": analysis_summary["pending_analyses"],
            "last_analysis_date": analysis_summary["last_analysis_date"],
            "usage_percentage": min(100, (current_month_analyses / 10) * 100)  # Assume free tier limit of 10
        }
        
    except Exception as e:
        logger.error("Get user usage endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user usage"
        )


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_change: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Change user password.
    
    Args:
        password_change: Password change request
        current_user_id: Current authenticated user ID
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        # Note: This functionality is not fully implemented in auth_service
        # but we call it to maintain consistency
        await auth_service.change_password(current_user_id, password_change.new_password)
        
    except Exception as e:
        logger.error("Change password endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )