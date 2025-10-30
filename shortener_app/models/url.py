from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from shortener_app.database.connection import Base


class URL(Base):
    """
    URL model for transactional data.
    
    This table stores ONLY core URL data (transactional).
    Analytics data is stored separately in ClickHouse/TimescaleDB.
    
    Separation of concerns:
    - Main DB (PostgreSQL/SQLite): Transactional data
    - Analytics DB (ClickHouse): Time-series hit data
    """
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    long_url = Column(String, nullable=False)
    # Note: unique=True automatically creates an index in SQLAlchemy (like Django)
    # Setting max length to 5 characters for short codes
    # Nullable=True allows two-step creation: first get ID, then generate short_code
    short_code = Column(String(5), unique=True, nullable=True, index=True)
    total_hits = Column(Integer, default=0)  # Aggregate count for quick stats
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
