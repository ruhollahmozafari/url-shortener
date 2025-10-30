"""
Message queue module for URL shortener.
Implements Strategy Pattern for flexible queue backends.
"""

from .strategies import QueueStrategy, RedisStreamQueue, InMemoryQueue
from .factory import QueueFactory
from .models import HitEvent

__all__ = [
    "QueueStrategy",
    "RedisStreamQueue",
    "InMemoryQueue",
    "QueueFactory",
    "HitEvent",
]

