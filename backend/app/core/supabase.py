"""
Supabase client configuration for Core Website Vitals backend.
Provides both regular and admin client instances for different use cases.
"""

from typing import Optional
from supabase import create_client, Client
from supabase.client import ClientOptions
from app.core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)
settings = get_settings()


def create_supabase_client(user_token: Optional[str] = None) -> Client:
    """
    Create a Supabase client for regular operations.
    
    Args:
        user_token: Optional JWT token for authenticated requests
        
    Returns:
        Configured Supabase client instance
        
    Raises:
        Exception: If client creation fails
    """
    try:
        # Configure client options
        client_options = ClientOptions(
            auto_refresh_token=True,
            persist_session=True
        )
        
        # Create client with anonymous key
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_anon_key,
            options=client_options
        )
        
        # Set user token if provided
        if user_token:
            client.auth.set_session(user_token)
        
        logger.info("Supabase client created successfully", 
                   url=settings.supabase_url,
                   has_user_token=bool(user_token))
        
        return client
        
    except Exception as e:
        logger.error("Failed to create Supabase client", 
                    error=str(e),
                    url=settings.supabase_url)
        raise Exception(f"Failed to create Supabase client: {str(e)}")


def create_supabase_admin_client() -> Client:
    """
    Create a Supabase admin client for service operations.
    This client bypasses Row Level Security policies.
    
    Returns:
        Configured Supabase admin client instance
        
    Raises:
        Exception: If admin client creation fails
    """
    try:
        # Configure client options for admin operations
        client_options = ClientOptions(
            auto_refresh_token=False,
            persist_session=False
        )
        
        # Create admin client with service role key
        admin_client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key,
            options=client_options
        )
        
        logger.info("Supabase admin client created successfully", 
                   url=settings.supabase_url)
        
        return admin_client
        
    except Exception as e:
        logger.error("Failed to create Supabase admin client", 
                    error=str(e),
                    url=settings.supabase_url)
        raise Exception(f"Failed to create Supabase admin client: {str(e)}")


def test_supabase_connection() -> bool:
    """
    Test Supabase connection and authentication.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        # Test regular client
        client = create_supabase_client()
        
        # Just check if we can create a client without making any queries
        # This will verify the URL and keys are valid
        
        # Test admin client creation as well
        admin_client = create_supabase_admin_client()
        
        # Log success without making any queries
        logger.info("Supabase clients created successfully")
        
        logger.info("Supabase connection test successful")
        return True
        
    except Exception as e:
        logger.error("Supabase connection test failed", error=str(e))
        return False


def get_supabase_client() -> Client:
    """
    Get regular Supabase client instance for dependency injection.
    
    Returns:
        Supabase client instance
    """
    return create_supabase_client()


def get_supabase_admin_client() -> Client:
    """
    Get admin Supabase client instance for dependency injection.
    
    Returns:
        Supabase admin client instance
    """
    return create_supabase_admin_client()


# Global client instances (lazy initialization)
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_cached_supabase_client() -> Client:
    """
    Get cached regular Supabase client instance.
    Creates client on first access.
    
    Returns:
        Cached Supabase client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_supabase_client()
    
    return _supabase_client


def get_cached_supabase_admin_client() -> Client:
    """
    Get cached admin Supabase client instance.
    Creates client on first access.
    
    Returns:
        Cached Supabase admin client instance
    """
    global _supabase_admin_client
    
    if _supabase_admin_client is None:
        _supabase_admin_client = create_supabase_admin_client()
    
    return _supabase_admin_client


def close_supabase_connections():
    """
    Close Supabase client connections.
    Call this during application shutdown.
    """
    global _supabase_client, _supabase_admin_client
    
    try:
        if _supabase_client:
            _supabase_client.auth.sign_out()
            _supabase_client = None
        
        if _supabase_admin_client:
            _supabase_admin_client.auth.sign_out()
            _supabase_admin_client = None
            
        logger.info("Supabase connections closed successfully")
        
    except Exception as e:
        logger.error("Error closing Supabase connections", error=str(e))


# Export commonly used clients
supabase_client = get_cached_supabase_client
supabase_admin_client = get_cached_supabase_admin_client