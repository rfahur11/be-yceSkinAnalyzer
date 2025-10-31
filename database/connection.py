"""
PostgreSQL database connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from config.settings import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=10,
    max_overflow=20
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def init_db():
    """
    Initialize database - create all tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db() -> Session:
    """
    Dependency untuk mendapatkan database session.
    Digunakan dengan FastAPI dependency injection.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager untuk database session.
    Digunakan dalam services yang tidak menggunakan FastAPI dependency.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
