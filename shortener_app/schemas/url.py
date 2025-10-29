from pydantic import BaseModel, HttpUrl, Field, computed_field, ConfigDict
from typing import Optional
from datetime import datetime
from shortener_app.config import settings


class URLBase(BaseModel):
    long_url: HttpUrl = Field(..., description="The original URL to be shortened")


class URLCreate(URLBase):
    pass


class URLResponse(URLBase):
    """Response schema that automatically serializes SQLAlchemy URL model
    
    This is like DRF's ModelSerializer!
    - from_attributes=True enables ORM mode (reads from model attributes)
    - @computed_field creates derived fields (like SerializerMethodField in DRF)
    """
    id: int
    short_code: str
    hits: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    @computed_field  # Like SerializerMethodField in DRF
    @property
    def short_url(self) -> str:
        """Computed field - automatically generated from short_code"""
        return f"{settings.base_url}/{self.short_code}"

    # Pydantic V2 style configuration
    model_config = ConfigDict(from_attributes=True)


class URLStats(BaseModel):
    short_code: str
    hits: int
    created_at: datetime
    last_accessed: Optional[datetime] = None

    # Pydantic V2 style configuration
    model_config = ConfigDict(from_attributes=True)
