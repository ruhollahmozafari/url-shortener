"""
Factory for creating cache instances.
Simple, clean factory with singleton caching.
"""

from enum import Enum
from .strategies import CacheStrategy, RedisCache, InMemoryCache, NullCache
from shortener_app.config import settings


class CacheBackend(Enum):
    """Available cache backends"""
    REDIS = "redis"
    MEMORY = "memory"
    NULL = "null"


class CacheFactory:
    """
    Simple factory for creating cache instances.
    
    Uses Singleton Pattern - creates instance once, reuses it.
    Gets configuration from settings (not passed as parameters).
    """
    
    _instance: CacheStrategy = None  # Single cached instance
    
    @classmethod
    def create(cls, backend: CacheBackend) -> CacheStrategy:
        """
        Create or return cached cache instance.
        
        Args:
            backend: Type of cache backend (from enum)
            
        Returns:
            Singleton cache instance
        """
        # Return cached instance if exists
        if cls._instance is not None:
            return cls._instance
        
        # Create new instance based on backend type
        if backend == CacheBackend.REDIS:
            import redis
            
            try:
                # Get Redis URL from settings (not from parameters!)
                redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=2,  # Reduced timeout
                    socket_timeout=2,          # Reduced timeout
                )
                
                # Test connection immediately
                redis_client.ping()
                
                cls._instance = RedisCache(redis_client)
                print(f"✅ Redis cache initialized")
                
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}")
                print(f"⚠️  Falling back to in-memory cache")
                cls._instance = InMemoryCache()
                print("✅ In-memory cache initialized (fallback)")
            
        elif backend == CacheBackend.MEMORY:
            cls._instance = InMemoryCache()
            print("✅ In-memory cache initialized")
            
        elif backend == CacheBackend.NULL:
            cls._instance = NullCache()
            print("✅ Null cache initialized")
            
        else:
            raise ValueError(f"Unknown cache backend: {backend}")
        
        return cls._instance
    
    @classmethod
    def clear_instance(cls):
        """Clear cached instance (for testing)"""
        cls._instance = None

