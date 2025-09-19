"""Configuration management using pydantic-settings."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Firecrawl API Configuration
    firecrawl_api_key: Optional[str] = Field(default=None, description="Firecrawl API key")
    
    # Environment
    env: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Application
    app_name: str = Field(default="smart_crawl", description="Application name")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Batch Processing
    batch_max_workers: int = Field(default=4, description="Maximum number of workers")
    batch_retry_count: int = Field(default=3, description="Number of retries for failed jobs")
    batch_timeout_seconds: int = Field(default=300, description="Job timeout in seconds")
    
    # Database (for future use)
    db_host: Optional[str] = Field(default=None, description="Database host")
    db_port: Optional[int] = Field(default=5432, description="Database port")
    db_name: Optional[str] = Field(default=None, description="Database name")
    db_user: Optional[str] = Field(default=None, description="Database user")
    db_password: Optional[str] = Field(default=None, description="Database password")
    
    # Redis (for future use)
    redis_host: Optional[str] = Field(default=None, description="Redis host")
    redis_port: Optional[int] = Field(default=6379, description="Redis port")
    redis_db: Optional[int] = Field(default=0, description="Redis database number")
    
    # API (for future use)
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    
    # External APIs
    api_key_service_1: Optional[str] = Field(default=None, description="API key for service 1")
    api_key_service_2: Optional[str] = Field(default=None, description="API key for service 2")
    
    # Notifications
    slack_webhook_url: Optional[str] = Field(default=None, description="Slack webhook URL")
    email_smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    email_smtp_port: Optional[int] = Field(default=587, description="SMTP port")
    email_from: Optional[str] = Field(default=None, description="From email address")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() == "development"
    
    @property
    def database_url(self) -> Optional[str]:
        """Build database URL from components."""
        if all([self.db_host, self.db_name, self.db_user, self.db_password]):
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        return None
    
    @property
    def redis_url(self) -> Optional[str]:
        """Build Redis URL from components."""
        if self.redis_host:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return None


# Create global settings instance
settings = Settings()