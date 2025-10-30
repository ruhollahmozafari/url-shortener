"""
FastAPI dependencies for dependency injection.

This module provides singleton instances of cache, queue, and hit storage
that are injected into services and routes.

Pattern: Dependency Injection
- Loose coupling between components
- Easy to test (inject mocks)
- Flexible (swap implementations via config)
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from shortener_app.cache.factory import CacheFactory, CacheBackend
from shortener_app.database.connection import get_db
from shortener_app.queue.factory import QueueFactory, QueueBackend
from shortener_app.storage.factory import HitStorageFactory, HitStorageBackend
from shortener_app.cache.strategies import CacheStrategy
from shortener_app.queue.strategies import QueueStrategy
from shortener_app.storage.strategies import HitStorageStrategy
from shortener_app.config import settings


@lru_cache()
def get_cache() -> CacheStrategy:
    """
    Get cache instance (singleton).
    
    Factory gets config from settings internally.
    @lru_cache ensures this is called only once.
    
    Returns:
        CacheStrategy instance based on settings
    """
    backend = CacheBackend(settings.cache_backend)
    return CacheFactory.create(backend)


@lru_cache()
def get_queue() -> QueueStrategy:
    """
    Get queue instance (singleton).
    
    Factory gets config from settings internally.
    @lru_cache ensures this is called only once.
    
    Returns:
        QueueStrategy instance based on settings
    """
    backend = QueueBackend(settings.queue_backend)
    return QueueFactory.create(backend)


@lru_cache()
def get_hit_storage() -> HitStorageStrategy:
    """
    Get hit storage instance (singleton).
    
    Factory gets config from settings internally.
    @lru_cache ensures this is called only once.
    
    Returns:
        HitStorageStrategy instance based on settings
    """
    backend = HitStorageBackend(settings.hit_storage_backend)
    return HitStorageFactory.create(backend)


def get_url_service(
    db: Session = Depends(get_db),
    cache: CacheStrategy = Depends(get_cache),
    queue: QueueStrategy = Depends(get_queue)
):
    """
    Get URLService with all dependencies injected.
    
    This is the RECOMMENDED pattern:
    - Controller depends on service
    - Service depends on infrastructure (db, cache, queue)
    
    Benefits:
    - Cleaner controllers (one dependency instead of three)
    - Easier to test (mock service, not individual deps)
    - Better separation of concerns
    """
    from shortener_app.services.url_service import URLService
    return URLService(db=db, cache=cache, queue=queue)

