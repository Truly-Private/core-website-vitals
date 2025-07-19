"""
Security utilities for Core Website Vitals backend.
Handles JWT token creation/validation and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT security scheme
security = HTTPBearer()


class JWTToken:
    """JWT token data structure."""
    
    def __init__(self, access_token: str, refresh_token: str, token_type: str = "bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug("Access token created successfully", 
                    subject=data.get("sub", "unknown"),
                    expires=expire.isoformat())
        
        return encoded_jwt
        
    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access token"
        )


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Token payload data
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        logger.debug("Refresh token created successfully", 
                    subject=data.get("sub", "unknown"),
                    expires=expire.isoformat())
        
        return encoded_jwt
        
    except Exception as e:
        logger.error("Failed to create refresh token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create refresh token"
        )


def create_token_pair(user_id: str, email: str, **extra_claims) -> JWTToken:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        email: User email
        **extra_claims: Additional claims to include in tokens
        
    Returns:
        JWTToken object containing both tokens
    """
    token_data = {
        "sub": user_id,
        "email": email,
        **extra_claims
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return JWTToken(
        access_token=access_token,
        refresh_token=refresh_token
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT access token without verification.
    
    Args:
        token: JWT access token
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            logger.warning("Invalid token type", expected="access", actual=payload.get("type"))
            return None
        
        return payload
        
    except JWTError as e:
        logger.warning("Token decoding failed", error=str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error during token decoding", error=str(e))
        return None


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify required claims
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.debug("Token verified successfully", 
                    user_id=user_id,
                    token_type=token_type)
        
        return payload
        
    except JWTError as e:
        logger.warning("Token verification failed", 
                      error=str(e),
                      token_type=token_type)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error("Unexpected error during token verification", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error("Failed to hash password", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to hash password"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        verified = pwd_context.verify(plain_password, hashed_password)
        logger.debug("Password verification completed", verified=verified)
        return verified
    except Exception as e:
        logger.error("Failed to verify password", error=str(e))
        return False


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current user ID from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        payload = verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get current user ID", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user payload from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Full token payload dictionary
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = verify_token(credentials.credentials, "access")
        return payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get current user payload", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


def refresh_access_token(refresh_token: str) -> str:
    """
    Create a new access token using a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token string
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = verify_token(refresh_token, "refresh")
        
        # Create new access token with same payload (minus token-specific claims)
        new_payload = {
            "sub": payload.get("sub"),
            "email": payload.get("email")
        }
        
        # Add any additional claims from original token
        for key, value in payload.items():
            if key not in ["exp", "iat", "type"]:
                new_payload[key] = value
        
        new_access_token = create_access_token(new_payload)
        
        logger.info("Access token refreshed successfully", 
                   user_id=payload.get("sub"))
        
        return new_access_token
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to refresh access token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


def validate_token_format(token: str) -> bool:
    """
    Validate JWT token format without verifying signature.
    
    Args:
        token: JWT token string
        
    Returns:
        True if format is valid, False otherwise
    """
    try:
        # JWT tokens should have 3 parts separated by dots
        parts = token.split('.')
        return len(parts) == 3
    except Exception:
        return False


# Optional: Rate limiting for auth endpoints
class AuthRateLimiter:
    """Simple in-memory rate limiter for authentication endpoints."""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if auth attempt is allowed for given identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                attempt for attempt in self.attempts[identifier] 
                if attempt > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self.attempts.get(identifier, []))
        
        if current_attempts >= self.max_attempts:
            return False
        
        # Record new attempt
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        self.attempts[identifier].append(now)
        
        return True


# Global rate limiter instance
auth_rate_limiter = AuthRateLimiter()