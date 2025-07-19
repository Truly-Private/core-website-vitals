"""
Authentication service for Core Website Vitals.
Handles user registration, login, profile management, and JWT token operations.
"""

from typing import Optional, Dict, Any
from supabase import Client
from fastapi import HTTPException, status, WebSocket, Depends
from app.core.security import (
    create_token_pair, 
    verify_password, 
    get_password_hash,
    refresh_access_token,
    auth_rate_limiter,
    JWTToken,
    security
)
from app.models.database import ProfilesTable
from app.models.schemas import (
    LoginRequest, 
    RegisterRequest, 
    UserResponse,
    UserUpdateRequest,
    SubscriptionTier
)
from app.services.email_service import EmailService
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.profiles = ProfilesTable(supabase_client)
        self.email_service = EmailService() if settings.ENABLE_EMAIL_NOTIFICATIONS else None
    
    async def register_user(
        self, 
        registration_data: RegisterRequest
    ) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth and create profile.
        
        Args:
            registration_data: User registration information
            
        Returns:
            Dictionary with user data and tokens
            
        Raises:
            HTTPException: If registration fails
        """
        try:
            # Check rate limiting
            if not auth_rate_limiter.is_allowed(registration_data.email):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many registration attempts. Please try again later."
                )
            
            # Register user with Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                "email": registration_data.email,
                "password": registration_data.password,
                "options": {
                    "data": {
                        "full_name": registration_data.full_name or ""
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed. Email may already be registered."
                )
            
            user = auth_response.user
            
            # Create profile record
            profile_data = await self.profiles.create_profile(
                user_id=user.id,
                email=registration_data.email,
                full_name=registration_data.full_name
            )
            
            if not profile_data:
                # If profile creation fails, we should clean up the auth user
                logger.error("Profile creation failed after successful auth registration",
                           user_id=user.id, email=registration_data.email)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Account creation failed. Please try again."
                )
            
            # Create JWT tokens
            tokens = create_token_pair(
                user_id=user.id,
                email=registration_data.email,
                full_name=registration_data.full_name or ""
            )
            
            logger.info("User registered successfully", 
                       user_id=user.id, 
                       email=registration_data.email)
            
            # Send welcome email if email service is enabled
            if self.email_service:
                try:
                    await self.email_service.send_welcome_email(
                        email=registration_data.email,
                        name=registration_data.full_name or registration_data.email.split('@')[0]
                    )
                    logger.info("Welcome email sent successfully", 
                               user_id=user.id, 
                               email=registration_data.email)
                except Exception as e:
                    # Don't fail registration if email sending fails
                    logger.error("Failed to send welcome email", 
                                user_id=user.id, 
                                email=registration_data.email,
                                error=str(e))
            
            return {
                "user": UserResponse(
                    id=user.id,
                    email=profile_data["email"],
                    full_name=profile_data["full_name"],
                    avatar_url=profile_data.get("avatar_url"),
                    subscription_tier=profile_data["subscription_tier"],
                    created_at=profile_data["created_at"],
                    updated_at=profile_data["updated_at"]
                ),
                "tokens": tokens
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User registration failed", 
                        email=registration_data.email, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed. Please try again."
            )
    
    async def login_user(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        Login user with email and password.
        
        Args:
            login_data: User login credentials
            
        Returns:
            Dictionary with user data and tokens
            
        Raises:
            HTTPException: If login fails
        """
        try:
            # Check rate limiting
            if not auth_rate_limiter.is_allowed(login_data.email):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please try again later."
                )
            
            # Authenticate with Supabase
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            user = auth_response.user
            
            # Get user profile
            profile_data = await self.profiles.get_profile(user.id)
            
            if not profile_data:
                logger.error("Profile not found for authenticated user", 
                           user_id=user.id, email=login_data.email)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            # Create JWT tokens
            tokens = create_token_pair(
                user_id=user.id,
                email=profile_data["email"],
                full_name=profile_data["full_name"] or ""
            )
            
            logger.info("User logged in successfully", 
                       user_id=user.id, 
                       email=login_data.email)
            
            return {
                "user": UserResponse(
                    id=user.id,
                    email=profile_data["email"],
                    full_name=profile_data["full_name"],
                    avatar_url=profile_data.get("avatar_url"),
                    subscription_tier=profile_data["subscription_tier"],
                    created_at=profile_data["created_at"],
                    updated_at=profile_data["updated_at"]
                ),
                "tokens": tokens
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User login failed", 
                        email=login_data.email, 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    
    async def refresh_token(self, refresh_token: str) -> str:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh fails
        """
        try:
            new_access_token = refresh_access_token(refresh_token)
            
            logger.info("Token refreshed successfully")
            return new_access_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to refresh token"
            )
    
    async def logout_user(self, user_id: str) -> bool:
        """
        Logout user by invalidating session.
        
        Args:
            user_id: User ID to logout
            
        Returns:
            True if logout successful
            
        Raises:
            HTTPException: If logout fails
        """
        try:
            # Sign out from Supabase
            self.supabase.auth.sign_out()
            
            logger.info("User logged out successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("User logout failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Logout failed"
            )
    
    async def get_current_user(self, user_id: str) -> UserResponse:
        """
        Get current user profile information.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile data
            
        Raises:
            HTTPException: If user not found
        """
        try:
            profile_data = await self.profiles.get_profile(user_id)
            
            if not profile_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse(
                id=profile_data["id"],
                email=profile_data["email"],
                full_name=profile_data["full_name"],
                avatar_url=profile_data.get("avatar_url"),
                subscription_tier=profile_data["subscription_tier"],
                created_at=profile_data["created_at"],
                updated_at=profile_data["updated_at"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Get current user failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user information"
            )
    
    async def update_user_profile(
        self, 
        user_id: str, 
        update_data: UserUpdateRequest
    ) -> UserResponse:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            update_data: Profile update data
            
        Returns:
            Updated user profile
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Prepare update data
            updates = {}
            if update_data.full_name is not None:
                updates["full_name"] = update_data.full_name
            if update_data.avatar_url is not None:
                updates["avatar_url"] = update_data.avatar_url
            
            if not updates:
                # No changes to make
                return await self.get_current_user(user_id)
            
            # Update profile
            updated_profile = await self.profiles.update_profile(user_id, updates)
            
            if not updated_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            logger.info("User profile updated successfully", 
                       user_id=user_id, 
                       updates=updates)
            
            return UserResponse(
                id=updated_profile["id"],
                email=updated_profile["email"],
                full_name=updated_profile["full_name"],
                avatar_url=updated_profile.get("avatar_url"),
                subscription_tier=updated_profile["subscription_tier"],
                created_at=updated_profile["created_at"],
                updated_at=updated_profile["updated_at"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User profile update failed", 
                        user_id=user_id, 
                        updates=update_data.dict(), 
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
    
    async def delete_user_account(self, user_id: str) -> bool:
        """
        Delete user account and all associated data.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Delete profile (this will cascade to delete analysis tasks due to foreign key)
            profile_deleted = await self.profiles.delete_profile(user_id)
            
            if not profile_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # TODO: Also delete from Supabase Auth
            # This requires admin privileges and should be handled carefully
            
            logger.info("User account deleted successfully", user_id=user_id)
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("User account deletion failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
    
    async def change_password(self, user_id: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If password change fails
        """
        try:
            # This would require updating the password in Supabase Auth
            # For now, we'll return a not implemented error
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Password change not yet implemented"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Password change failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    async def verify_user_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and return user information.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token verification result
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            from app.core.security import verify_token
            
            payload = verify_token(token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Get user profile to ensure user still exists
            profile_data = await self.profiles.get_profile(user_id)
            
            if not profile_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return {
                "valid": True,
                "user_id": user_id,
                "email": payload.get("email"),
                "expires_at": payload.get("exp")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


def get_auth_service(supabase_client: Client) -> AuthService:
    """
    Get AuthService instance for dependency injection.
    
    Args:
        supabase_client: Supabase client instance
        
    Returns:
        AuthService instance
    """
    return AuthService(supabase_client)


async def get_current_user(token: str = Depends(security)):
    """
    Get current user from JWT token.
    
    Args:
        token: JWT access token
        
    Returns:
        User information
    """
    from app.core.security import get_current_user_payload
    from app.core.supabase import get_cached_supabase_client
    
    # Get user ID from token
    user_payload = get_current_user_payload(token)
    user_id = user_payload.get("sub")
    
    # Get user profile
    supabase_client = get_cached_supabase_client()
    auth_service = AuthService(supabase_client)
    
    return await auth_service.get_current_user(user_id)


async def get_current_user_websocket(token: str) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token for WebSocket authentication.
    
    Args:
        token: JWT access token
        
    Returns:
        User information if token is valid, None otherwise
    """
    try:
        from app.core.security import verify_token
        from app.core.supabase import get_cached_supabase_client
        
        # Verify token
        payload = verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Get user profile
        supabase_client = get_cached_supabase_client()
        auth_service = AuthService(supabase_client)
        
        profile_data = await auth_service.profiles.get_profile(user_id)
        
        if not profile_data:
            return None
        
        return {
            "id": user_id,
            "email": profile_data["email"],
            "full_name": profile_data["full_name"],
            "subscription_tier": profile_data["subscription_tier"]
        }
        
    except Exception as e:
        logger.error("WebSocket authentication failed", error=str(e))
        return None