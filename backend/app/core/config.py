"""
Pydantic Settings configuration for Core Website Vitals backend.
Environment variables are loaded automatically from .env file.
"""

from typing import List, Optional, Union
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with automatic environment variable loading."""
    
    # Application Configuration
    APP_NAME: str = "Core Website Vitals"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    
    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_RELOAD: bool = False
    
    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = Field(default=["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Local Supabase Configuration (for development)
    LOCAL_SUPABASE_URL: Optional[str] = None
    LOCAL_SUPABASE_ANON_KEY: Optional[str] = None
    LOCAL_SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_MAX_RETRIES: int = 3
    CELERY_RETRY_DELAY: int = 60
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_TIME_LIMIT: int = 600  # 10 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540  # 9 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    
    # Timezone
    TIMEZONE: str = "UTC"
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "info"
    LOG_FORMAT: str = "json"
    
    # Security Configuration
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Feature Flags
    ENABLE_REAL_TIME_UPDATES: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    
    # Email Configuration (Resend)
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "noreply@corewebsitevitals.com"
    EMAIL_FROM_NAME: str = "Core Website Vitals"
    
    # External Services
    SENTRY_DSN: Optional[str] = None
    ANALYTICS_API_KEY: Optional[str] = None
    
    # SEO Analysis Configuration
    SEO_ANALYSIS_TIMEOUT: int = 300  # 5 minutes
    SEO_ANALYSIS_MAX_CONCURRENT: int = 10
    SEO_ANALYSIS_RATE_LIMIT: int = 100
    
    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_DOMAIN: str = "localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if v is None:
            return ["http://localhost:3000"]
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if v is None:
            return ["localhost", "127.0.0.1"]
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        if isinstance(v, list):
            return v
        return ["localhost", "127.0.0.1"]
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.lower()
    
    @field_validator("LOG_FORMAT")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"LOG_FORMAT must be one of {valid_formats}")
        return v.lower()
    
    @field_validator("SEO_ANALYSIS_TIMEOUT")
    @classmethod
    def validate_seo_timeout(cls, v):
        """Validate SEO analysis timeout."""
        if v < 30 or v > 600:  # 30 seconds to 10 minutes
            raise ValueError("SEO_ANALYSIS_TIMEOUT must be between 30 and 600 seconds")
        return v
    
    @field_validator("CELERY_WORKER_CONCURRENCY")
    @classmethod
    def validate_celery_concurrency(cls, v):
        """Validate Celery worker concurrency."""
        if v < 1 or v > 20:
            raise ValueError("CELERY_WORKER_CONCURRENCY must be between 1 and 20")
        return v
    
    @property
    def database_url(self) -> str:
        """Get database URL from Supabase if DATABASE_URL not set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Extract database URL from Supabase URL
        # This is a simplified approach - in production you'd use connection pooling
        return f"postgresql://postgres:[PASSWORD]@{self.SUPABASE_URL.split('//')[1]}/postgres"
    
    @property
    def redis_url_with_password(self) -> str:
        """Get Redis URL with password if provided."""
        if self.REDIS_PASSWORD:
            return self.REDIS_URL.replace("://", f"://:{self.REDIS_PASSWORD}@")
        return self.REDIS_URL
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return not self.DEBUG and not self.TESTING
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.DEBUG and not self.TESTING
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.TESTING
    
    @property
    def supabase_url(self) -> str:
        """Get Supabase URL (use local in development)."""
        if self.DEBUG and self.LOCAL_SUPABASE_URL:
            return self.LOCAL_SUPABASE_URL
        return self.SUPABASE_URL
    
    @property
    def supabase_anon_key(self) -> str:
        """Get Supabase anon key (use local in development)."""
        if self.DEBUG and self.LOCAL_SUPABASE_ANON_KEY:
            return self.LOCAL_SUPABASE_ANON_KEY
        return self.SUPABASE_ANON_KEY
    
    @property
    def supabase_service_role_key(self) -> str:
        """Get Supabase service role key (use local in development)."""
        if self.DEBUG and self.LOCAL_SUPABASE_SERVICE_ROLE_KEY:
            return self.LOCAL_SUPABASE_SERVICE_ROLE_KEY
        return self.SUPABASE_SERVICE_ROLE_KEY


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection."""
    return settings