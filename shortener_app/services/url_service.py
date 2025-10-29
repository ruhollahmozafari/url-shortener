import string
import random
from typing import Union

from pydantic import HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy import update
from shortener_app.models.url import URL
from shortener_app.schemas.url import URLResponse, URLStats
from shortener_app.config import settings


class URLService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_short_code(self, length: int = None) -> str:
        """Generate a random short code"""
        if length is None:
            length = settings.short_url_length

        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def _get_unique_short_code(self) -> str:
        """Generate a unique short code"""
        for _ in range(settings.max_retries):
            short_code = self._generate_short_code()
            if not self.db.query(URL).filter(URL.short_code == short_code).first():
                return short_code
        raise Exception("Could not generate unique short code")

    def create_short_url(self, long_url: HttpUrl) -> URL:
        """Create a new short URL
        
        Note: Always creates a new short URL even if the long URL already exists.
        This allows tracking different sources/campaigns for the same destination URL.
        
        Returns the SQLAlchemy model instance - Pydantic will auto-serialize it!
        """
        # Always create new short URL for analytics tracking
        short_code = self._get_unique_short_code()
        url = URL(
            long_url=str(long_url),
            short_code=short_code
        )

        self.db.add(url)
        self.db.commit()
        self.db.refresh(url)

        # Return the model instance directly!
        # Pydantic will automatically serialize it using from_attributes=True
        return url

    def get_url_by_short_code(self, short_code: str) -> Union[URL, None]:
        """Get URL by short code
        
        Returns SQLAlchemy model instance or None.
        Pydantic will auto-serialize it to URLResponse schema.
        """
        url = self.db.query(URL).filter(
            URL.short_code == short_code,
            URL.is_active == True
        ).first()

        # Return the model instance directly (or None)
        # Just like DRF: serializer = URLSerializer(url) → url gets serialized automatically
        return url

    def redirect_url(self, short_code: str) -> str:
        """Get the long URL for redirection and increment hit count
        
        Performance optimization: Uses UPDATE statement to increment counter
        without loading the full object into memory (atomic operation).
        This is much more efficient than fetch -> increment -> save.
        """
        url = self.db.query(URL).filter(
            URL.short_code == short_code,
            URL.is_active == True
        ).first()

        if not url:
            return None

        # Performance: Atomic increment using SQL UPDATE (like Django's F() expressions)
        # This is equivalent to: URL.objects.filter(short_code=short_code).update(hits=F('hits') + 1)
        self.db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(hits=URL.hits + 1)
        )
        self.db.commit()

        return url.long_url

    def get_url_stats(self, short_code: str) -> URLStats:
        """Get statistics for a short URL"""
        url = self.db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            return None

        return URLStats(
            short_code=url.short_code,
            hits=url.hits,
            created_at=url.created_at,
            last_accessed=url.updated_at
        )

    def delete_url(self, short_code: str) -> bool:
        """Delete a short URL (soft delete)"""
        url = self.db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            return False

        url.is_active = False
        self.db.commit()
        return True
