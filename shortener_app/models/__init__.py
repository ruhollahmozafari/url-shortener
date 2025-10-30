"""
Database models for URL shortener.

Note: Analytics data (hit events) is stored in separate database (ClickHouse/TimescaleDB),
not in SQLAlchemy models. This separates transactional data from analytical data.
"""

from .url import URL

__all__ = ["URL"]

