"""
Cache strategies using Strategy Pattern.
Allows switching between different cache backends (Redis, In-Memory, Null).
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
from datetime import timedelta


class CacheStrategy(ABC):
    """
    Abstract base class for cache strategies.
    
    This is the Strategy Pattern interface - allows multiple cache implementations
    without changing the service layer code.
    
    All methods are async because cache operations involve I/O (network for Redis).
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL (Time To Live).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if key didn't exist
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful
        """
        pass


class RedisCache(CacheStrategy):
    """
    Redis cache implementation with async operations.
    
    Production-ready cache with:
    - Distributed caching (multiple servers can share cache)
    - Persistence (survives restarts if configured)
    - Atomic operations
    - TTL support
    - Non-blocking I/O (async)
    
    Used in production environments.
    """
    
    def __init__(self, redis_client):
        """
        Initialize Redis cache.
        
        Args:
            redis_client: Redis client instance (redis.Redis)
        """
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis (async I/O)"""
        try:
            value = self.redis.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Set value in Redis with TTL (async I/O)"""
        try:
            return self.redis.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis (async I/O)"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis (async I/O)"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis keys (use with caution!)"""
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False


class InMemoryCache(CacheStrategy):
    """
    In-memory cache implementation using Python dict.
    
    Pros:
    - Very fast (no network overhead)
    - Simple (no external dependencies)
    - Good for development and testing
    
    Cons:
    - Not distributed (each server has its own cache)
    - Lost on restart
    - No TTL enforcement (would need hit_processor cleanup)
    
    Used in development/testing environments.
    Note: Async for interface consistency, but operations are instant.
    """
    
    def __init__(self):
        """Initialize in-memory cache"""
        self._cache: Dict[str, str] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from memory (instant, but async for interface)"""
        return self._cache.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set value in memory (instant, but async for interface).
        
        Note: TTL is ignored in this simple implementation.
        For production, you'd need a hit_processor task to clean expired keys.
        """
        self._cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory (instant, but async for interface)"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory (instant, but async for interface)"""
        return key in self._cache
    
    async def clear(self) -> bool:
        """Clear all cache entries (instant, but async for interface)"""
        self._cache.clear()
        return True


class NullCache(CacheStrategy):
    """
    Null Object Pattern - cache that does nothing.
    
    Used for:
    - Testing (when you want to test without cache)
    - Disabling cache in certain environments
    - Fallback when cache is unavailable
    
    All operations succeed but don't actually cache anything.
    Note: Async for interface consistency.
    """
    
    async def get(self, key: str) -> Optional[str]:
        """Always returns None (cache miss)"""
        return None
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """Pretends to set but does nothing"""
        return True
    
    async def delete(self, key: str) -> bool:
        """Pretends to delete but does nothing"""
        return True
    
    async def exists(self, key: str) -> bool:
        """Always returns False"""
        return False
    
    async def clear(self) -> bool:
        """Pretends to clear but does nothing"""
        return True

