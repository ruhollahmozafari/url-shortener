from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Application
    app_name: str = "URL Shortener"
    app_version: str = "1.0.0"
    secret_key: str = "your-secret-key-here-change-in-production"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./url_shortener.db"
    
    # URL Shortener specific
    base_url: str = "http://127.0.0.1:8000"
    short_url_length: int = 5  # Max 5 characters for short codes
    max_retries: int = 5
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()
