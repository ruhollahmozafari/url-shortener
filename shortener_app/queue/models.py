"""
Data models for queue messages.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class HitEvent(BaseModel):
    """
    Event model for URL hit tracking.
    
    This is published to the queue when a user accesses a short URL.
    Contains all metadata needed for analytics.
    """
    
    short_code: str = Field(..., description="The short code that was accessed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the hit occurred")
    
    # Request metadata
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    referer: Optional[str] = Field(None, description="HTTP referer")
    
    # Parsed metadata (can be enriched by worker)
    country: Optional[str] = Field(None, description="Country code (e.g., US, UK)")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    browser: Optional[str] = Field(None, description="Browser name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "short_code": "abc12",
                "timestamp": "2025-10-29T10:30:00",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
                "referer": "https://twitter.com",
                "country": "US",
                "device_type": "desktop",
                "browser": "Chrome"
            }
        }

