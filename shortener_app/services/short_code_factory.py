"""
Factory for creating short code generation strategies.
Uses caching to avoid creating multiple instances.
"""

from enum import Enum
from shortener_app.services.short_code_strategies import (
    ShortCodeStrategy,
    RandomShortCodeStrategy,
    Base62ShortCodeStrategy
)
from shortener_app.config import settings


class ShortCodeStrategyType(Enum):
    """Available short code generation strategies"""
    RANDOM = "random"
    BASE62 = "base62"


class ShortCodeFactory:
    """Factory for creating short code generation strategies with caching"""
    
    _instances = {}  # Cache for strategy instances
    
    @classmethod
    def create_strategy(
        cls,
        strategy_type: ShortCodeStrategyType = None
    ) -> ShortCodeStrategy:
        """
        Create or return cached short code generation strategy.
        Uses singleton pattern to avoid creating multiple instances.
        
        Args:
            strategy_type: Type of strategy to create.
                          If None, uses value from settings.
        
        Returns:
            A cached instance of a ShortCodeStrategy
        
        Raises:
            ValueError: If strategy_type is unknown
        """
        # Use default from settings if not specified
        if strategy_type is None:
            strategy_type = ShortCodeStrategyType(settings.short_code_strategy)
        
        # Return cached instance if exists
        if strategy_type in cls._instances:
            return cls._instances[strategy_type]
        
        # Create new instance and cache it
        if strategy_type == ShortCodeStrategyType.RANDOM:
            instance = RandomShortCodeStrategy(
                length=settings.short_url_length,
                max_retries=settings.max_retries
            )
        elif strategy_type == ShortCodeStrategyType.BASE62:
            instance = Base62ShortCodeStrategy(
                salt=settings.short_code_salt,
                max_length=settings.short_url_length
            )
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # Cache the instance
        cls._instances[strategy_type] = instance
        return instance
