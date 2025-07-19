"""
Authentication endpoints for Core Website Vitals API.
Handles user registration, login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import get_current_user_id, security
from app.core.supabase import get_cached_supabase_client
from app.services.auth_service import get_auth_service
from app.models.schemas import (
    LoginRequest, 
    RegisterRequest, 
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    Args:
        request: User registration data
        
    Returns:
        JWT tokens for the new user
    """
    try:
        # Use admin client for registration to bypass RLS
        from app.core.supabase import get_cached_supabase_admin_client
        supabase_client = get_cached_supabase_admin_client()
        auth_service = get_auth_service(supabase_client)
        
        result = await auth_service.register_user(request)
        
        return TokenResponse(
            access_token=result["tokens"].access_token,
            refresh_token=result["tokens"].refresh_token,
            token_type=result["tokens"].token_type,
            expires_in=result["tokens"].expires_in
        )
        
    except Exception as e:
        logger.error("Registration endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Args:
        request: Login credentials
        
    Returns:
        JWT tokens for authenticated user
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        result = await auth_service.login_user(request)
        
        return TokenResponse(
            access_token=result["tokens"].access_token,
            refresh_token=result["tokens"].refresh_token,
            token_type=result["tokens"].token_type,
            expires_in=result["tokens"].expires_in
        )
        
    except Exception as e:
        logger.error("Login endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        New access token
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        new_access_token = await auth_service.refresh_token(request.refresh_token)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except Exception as e:
        logger.error("Token refresh endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user_id: str = Depends(get_current_user_id)):
    """
    Logout current user.
    
    Args:
        current_user_id: Current authenticated user ID
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        await auth_service.logout_user(current_user_id)
        
    except Exception as e:
        logger.error("Logout endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user_id: str = Depends(get_current_user_id)):
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


@router.post("/verify-token")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token validity.
    
    Args:
        credentials: JWT token credentials
        
    Returns:
        Token verification status
    """
    try:
        supabase_client = get_cached_supabase_client()
        auth_service = get_auth_service(supabase_client)
        
        verification_result = await auth_service.verify_user_token(credentials.credentials)
        return verification_result
        
    except Exception as e:
        logger.error("Token verification endpoint failed", error=str(e))
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )