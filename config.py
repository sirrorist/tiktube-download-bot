"""Configuration module for the bot."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Bot Configuration
    bot_token: str = Field(..., env="BOT_TOKEN")
    bot_username: Optional[str] = Field(default=None, env="BOT_USERNAME")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="content_downloader", env="POSTGRES_DB")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Application Settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    temp_dir: str = Field(default="./temp", env="TEMP_DIR")
    storage_dir: str = Field(default="./storage", env="STORAGE_DIR")
    
    # Rate Limiting
    free_user_limit: int = Field(default=7, env="FREE_USER_LIMIT")
    premium_user_limit: int = Field(default=1000, env="PREMIUM_USER_LIMIT")
    
    # API Keys
    twitter_api_key: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    twitter_api_secret: Optional[str] = Field(default=None, env="TWITTER_API_SECRET")
    instagram_username: Optional[str] = Field(default=None, env="INSTAGRAM_USERNAME")
    instagram_password: Optional[str] = Field(default=None, env="INSTAGRAM_PASSWORD")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    webhook_url: Optional[str] = Field(default=None, env="WEBHOOK_URL")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
