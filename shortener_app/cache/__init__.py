"""
Cache module for URL shortener.
Implements Strategy Pattern for flexible cache backends.
"""

from .strategies import CacheStrategy, RedisCache, InMemoryCache, NullCache
from .factory import CacheFactory

__all__ = [
    "CacheStrategy",
    "RedisCache", 
    "InMemoryCache",
    "NullCache",
    "CacheFactory",
]

