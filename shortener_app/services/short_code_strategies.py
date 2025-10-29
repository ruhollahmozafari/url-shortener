"""
Short code generation strategies for URL shortener.
Uses Strategy Pattern to allow different generation algorithms.
"""

import string
import random
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from shortener_app.models.url import URL


class ShortCodeStrategy(ABC):
    """Abstract base class for short code generation strategies"""
    
    @abstractmethod
    def generate(self, url_id: int, db_session: Session) -> str:
        """
        Generate a short code.
        
        Args:
            url_id: The database ID of the URL record
            db_session: Database session for strategies that need to check uniqueness
            
        Returns:
            A unique short code string
        """
        pass


class RandomShortCodeStrategy(ShortCodeStrategy):
    """
    Original random generation strategy.
    Generates random string and checks database for uniqueness.
    
    Pros: Simple, unpredictable
    Cons: Collision risk, multiple DB queries, not scalable
    """
    
    def __init__(self, length: int = 5, max_retries: int = 5):
        self.length = length
        self.max_retries = max_retries
        self.characters = string.ascii_letters + string.digits
    
    def generate(self, url_id: int, db_session: Session) -> str:
        """Generate random short code with collision checking"""
        for attempt in range(self.max_retries):
            short_code = self._generate_random_string()
            
            # Check if code already exists
            if not db_session.query(URL).filter(URL.short_code == short_code).first():
                return short_code
        
        # If all retries failed
        raise Exception(
            f"Could not generate unique short code after {self.max_retries} attempts"
        )
    
    def _generate_random_string(self) -> str:
        """Generate a random string of specified length"""
        return ''.join(random.choice(self.characters) for _ in range(self.length))


class Base62ShortCodeStrategy(ShortCodeStrategy):
    """
    Base62 encoding strategy with ID obfuscation.
    Converts auto-increment ID to Base62 with salt for security.
    
    Pros: No collisions, fast, scalable, no DB queries
    Cons: Predictable if salt is known (but obfuscated)
    """
    
    BASE62_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self, salt: int = 1000, max_length: int = 5):
        self.salt = salt
        self.max_length = max_length
    
    def generate(self, url_id: int, db_session: Session) -> str:
        """
        Generate short code using Base62 encoding.
        
        Process:
        1. Add salt to ID for obfuscation
        2. Encode to Base62
        3. Return encoded string (no padding/truncation)
        
        Note: If encoded string exceeds max_length, raise error.
        This indicates salt is too small for the URL volume.
        """
        # Obfuscate the ID with salt
        obfuscated_id = url_id + self.salt
        
        # Convert to Base62
        encoded = self._base62_encode(obfuscated_id)
        
        # Check if exceeds max length (this would cause duplicates if truncated)
        if len(encoded) > self.max_length:
            raise ValueError(
                f"Generated code '{encoded}' exceeds max length {self.max_length}. "
                f"URL ID: {url_id}, Obfuscated ID: {obfuscated_id}. "
                f"Consider increasing salt or max_length to handle higher volume."
            )
        
        return encoded
    
    def _base62_encode(self, number: int) -> str:
        """
        Convert integer to Base62 string.
        
        Base62 uses: 0-9 (10) + a-z (26) + A-Z (26) = 62 characters
        This is more compact than Base10 and URL-safe.
        """
        if number == 0:
            return self.BASE62_CHARS[0]
        
        result = ""
        while number > 0:
            result = self.BASE62_CHARS[number % 62] + result
            number //= 62
        
        return result
