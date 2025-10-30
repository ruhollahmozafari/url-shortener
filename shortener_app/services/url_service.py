from typing import Union, Optional

from pydantic import HttpUrl
from sqlalchemy.orm import Session
from sqlalchemy import update
from shortener_app.models.url import URL
from shortener_app.schemas.url import URLResponse, URLStats
from shortener_app.config import settings
from shortener_app.services.short_code_factory import ShortCodeFactory
from shortener_app.services.short_code_strategies import ShortCodeStrategy
from shortener_app.cache.strategies import CacheStrategy
from shortener_app.queue.strategies import QueueStrategy


class URLService:
    """
    URL Service with dependency injection for cache and queue.
    
    This follows the Dependency Injection pattern:
    - Cache and queue strategies are injected (not created internally)
    - Easy to test (inject mock cache/queue)
    - Flexible (swap implementations without changing code)
    
    Similar to Django's service layer pattern.
    """
    
    def __init__(
        self, 
        db: Session,
        cache: Optional[CacheStrategy] = None,
        queue: Optional[QueueStrategy] = None
    ):
        """
        Initialize URL service with dependencies.
        
        Args:
            db: Database session
            cache: Cache strategy (optional, for performance)
            queue: Queue strategy (optional, for async hit tracking)
        """
        self.db = db
        self.cache = cache
        self.queue = queue
        # Use provided strategy or create default from factory
        self.short_code_strategy = ShortCodeFactory.create_strategy()

    async def create_short_url(self, long_url: HttpUrl) -> URL:
        """Create a new short URL
        
        Note: Always creates a new short URL even if the long URL already exists.
        This allows tracking different sources/campaigns for the same destination URL.
        
        Process:
        1. Create URL with placeholder short_code to get auto-increment ID
        2. Generate actual short_code using ID
        3. Update with final short_code
        4. Cache the mapping (async I/O - non-blocking)
        
        Returns the SQLAlchemy model instance - Pydantic will auto-serialize it!
        
        Note: This is async because of cache.set() (Redis I/O).
        Database operations are still sync - that's fine!
        """
        # Create URL record with placeholder to get auto-increment ID
        # The short_code can be None (nullable) during creation
        url = URL(long_url=str(long_url), short_code=None)
        self.db.add(url)
        self.db.flush()  # Flush to get ID without committing (sync - fast)
        
        # Now url.id is available - generate short code using strategy
        url.short_code = self.short_code_strategy.generate(url.id, self.db)
        
        # Commit with final short code (sync - fast)
        self.db.commit()
        self.db.refresh(url)
        
        # Cache the mapping for fast lookups (async - non-blocking!)
        if self.cache:
            cache_key = f"url:{url.short_code}"
            await self.cache.set(cache_key, url.long_url, ttl=settings.cache_ttl)

        # Return the model instance directly!
        # Pydantic will automatically serialize it using from_attributes=True
        return url

    async def get_url_by_short_code(self, short_code: str) -> Union[URL, None]:
        """Get URL by short code
        
        Returns SQLAlchemy model instance or None.
        Pydantic will auto-serialize it to URLResponse schema.
        
        Note: Async for interface consistency, DB query is sync (fast).
        """
        url = self.db.query(URL).filter(
            URL.short_code == short_code,
            URL.is_active == True
        ).first()
        
        # Return the model instance directly (or None)
        # Just like DRF: serializer = URLSerializer(url) → url gets serialized automatically
        return url

    async def get_long_url_for_redirect(self, short_code: str) -> Optional[str]:
        """
        Get long URL for redirection using Cache-Aside pattern.
        
        This method ONLY retrieves the URL (doesn't track hits).
        Hit tracking is done separately via queue for better performance.
        
        Flow:
        1. Check cache first (async I/O - ~0.1ms)
        2. If cache miss, query database (sync - ~2ms)
        3. Populate cache for next time (async I/O - ~0.1ms)
        4. Return long URL
        
        Performance: ~0.1ms for cache hit, ~2ms for cache miss
        
        Note: Async for cache I/O, DB query is sync (mixing is fine!)
        """
        cache_key = f"url:{short_code}"
        
        # Step 1: Try cache first (Cache-Aside Pattern) - ASYNC I/O
        if self.cache:
            cached_url = await self.cache.get(cache_key)
            if cached_url:
                # Cache HIT - return immediately
                return cached_url
        
        # Step 2: Cache MISS - query database (SYNC - fast with indexes)
        url = self.db.query(URL).filter(
            URL.short_code == short_code,
            URL.is_active == True
        ).first()
        
        if not url:
            return None
        
        # Step 3: Populate cache for next time - ASYNC I/O
        if self.cache:
            await self.cache.set(cache_key, url.long_url, ttl=settings.cache_ttl)
        
        # Step 4: Return long URL
        return url.long_url

    async def get_url_stats(self, short_code: str) -> Optional[URLStats]:
        """Get statistics for a short URL
        
        Note: Async for interface consistency, DB query is sync (fast).
        """
        url = self.db.query(URL).filter(URL.short_code == short_code).first()

        if not url:
            return None

        return URLStats(
            short_code=url.short_code,
            total_hits=url.total_hits,  # Use total_hits instead of hits
            created_at=url.created_at,
            last_accessed=url.updated_at
        )

    async def delete_url(self, short_code: str) -> bool:
        """
        Delete a short URL (soft delete).
        Also invalidates cache (async I/O).
        """
        url = self.db.query(URL).filter(URL.short_code == short_code).first()
        
        if not url:
            return False
        
        url.is_active = False
        self.db.commit()
        
        # Invalidate cache (async I/O)
        if self.cache:
            cache_key = f"url:{short_code}"
            await self.cache.delete(cache_key)
        
        return True
