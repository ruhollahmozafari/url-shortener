"""
Hit storage module for analytics data.

This module implements the Strategy Pattern for pluggable analytics storage.
Separates transactional data (main DB) from analytical data (specialized DB).
"""

from .strategies import HitStorageStrategy, SQLiteHitStorage, ClickHouseHitStorage
from .factory import HitStorageFactory, HitStorageBackend

__all__ = [
    "HitStorageStrategy",
    "SQLiteHitStorage",
    "ClickHouseHitStorage",
    "HitStorageFactory",
    "HitStorageBackend",
]

