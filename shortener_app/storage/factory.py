"""
Factory for creating hit storage instances.
Simple, clean factory with singleton caching.
"""

from enum import Enum
from .strategies import HitStorageStrategy, SQLiteHitStorage, ClickHouseHitStorage
from shortener_app.config import settings


class HitStorageBackend(Enum):
    """Available hit storage backends"""
    SQLITE = "sqlite"
    CLICKHOUSE = "clickhouse"


class HitStorageFactory:
    """
    Simple factory for creating hit storage instances.
    
    Gets configuration from settings (not passed as parameters).
    """
    
    _instance: HitStorageStrategy = None  # Single cached instance
    
    @classmethod
    def create(cls, backend: HitStorageBackend) -> HitStorageStrategy:
        """
        Create or return cached hit storage instance.
        
        Args:
            backend: Type of storage backend (from enum)
            
        Returns:
            Singleton hit storage instance
        """
        # Return cached instance if exists
        if cls._instance is not None:
            return cls._instance
        
        # Create new instance based on backend type
        if backend == HitStorageBackend.SQLITE:
            cls._instance = SQLiteHitStorage(db_path=settings.hit_storage_sqlite_path)
            print(f"✅ SQLite hit storage initialized")
            
        elif backend == HitStorageBackend.CLICKHOUSE:
            cls._instance = ClickHouseHitStorage(
                url=settings.hit_storage_clickhouse_url,
                buffer_size=settings.hit_storage_buffer_size
            )
            print(f"✅ ClickHouse hit storage initialized (interface only)")
            
        else:
            raise ValueError(f"Unknown storage backend: {backend}")
        
        return cls._instance
    
    @classmethod
    def clear_instance(cls):
        """Clear cached instance (for testing)"""
        cls._instance = None

