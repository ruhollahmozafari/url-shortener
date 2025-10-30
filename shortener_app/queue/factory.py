"""
Factory for creating queue instances.
Simple, clean factory with singleton caching.
"""

from enum import Enum
from .strategies import QueueStrategy, RedisStreamQueue, InMemoryQueue
from shortener_app.config import settings


class QueueBackend(Enum):
    """Available queue backends"""
    REDIS_STREAMS = "redis_streams"
    MEMORY = "memory"


class QueueFactory:
    """
    Simple factory for creating queue instances.
    
    Gets configuration from settings (not passed as parameters).
    """
    
    _instance: QueueStrategy = None  # Single cached instance
    
    @classmethod
    def create(cls, backend: QueueBackend) -> QueueStrategy:
        """
        Create or return cached queue instance.
        
        Args:
            backend: Type of queue backend (from enum)
            
        Returns:
            Singleton queue instance
        """
        # Return cached instance if exists
        if cls._instance is not None:
            return cls._instance
        
        # Create new instance based on backend type
        if backend == QueueBackend.REDIS_STREAMS:
            import redis
            
            # Get config from settings
            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            
            cls._instance = RedisStreamQueue(
                redis_client,
                settings.queue_consumer_group
            )
            print("✅ Redis queue initialized")
            
        elif backend == QueueBackend.MEMORY:
            cls._instance = InMemoryQueue()
            print("✅ In-memory queue initialized")
            
        else:
            raise ValueError(f"Unknown queue backend: {backend}")
        
        return cls._instance
    
    @classmethod
    def clear_instance(cls):
        """Clear cached instance (for testing)"""
        cls._instance = None

