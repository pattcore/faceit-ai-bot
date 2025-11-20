"""
Database configuration and SQLAlchemy setup
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(str(Path(__file__).parent))
from config.settings import settings

# Creation engine factory
if settings.DATABASE_URL.startswith("sqlite"):
    def _create_engine():
        return create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
else:
    def _create_engine():
        return create_engine(settings.DATABASE_URL)

# Global engine for backward compatibility (not used in get_db)
engine = _create_engine()

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    """
    engine = _create_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
