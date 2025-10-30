from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Loading priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. Default values below
    """
    
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
    
    # Short code generation strategy
    short_code_strategy: str = "base62"  # Options: "random", "base62"
    short_code_salt: int = 1256  # Salt for Base62 strategy (4 digits)
    
    # Cache settings
    cache_backend: str = "redis"  # Options: "redis", "memory", "null"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600  # Cache TTL in seconds (1 hour)
    
    # Queue settings
    queue_backend: str = "redis_streams"  # Options: "redis_streams", "memory"
    queue_name: str = "url_hits"
    queue_consumer_group: str = "url_workers"
    queue_batch_size: int = 100  # Number of messages to process at once
    queue_worker_interval: int = 5  # Worker poll interval in seconds
    
    # Hit Storage settings (Analytics Database)
    hit_storage_backend: str = "sqlite"  # Options: "sqlite", "clickhouse"
    hit_storage_sqlite_path: str = "analytics.db"  # SQLite database path
    hit_storage_clickhouse_url: str = "http://localhost:8123"  # ClickHouse HTTP endpoint
    hit_storage_buffer_size: int = 1000  # Buffer size for batching (ClickHouse)
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Create settings instance
settings = Settings()
