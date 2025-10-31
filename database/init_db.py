"""
Database initialization and migration script
Run this script to create all database tables
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import init_db, engine
from database.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Initialize database schema
    """
    try:
        logger.info("Starting database initialization...")
        logger.info(f"Database URL: {engine.url}")
        
        # Create all tables
        init_db()
        
        logger.info("✓ Database initialized successfully!")
        logger.info("Tables created:")
        logger.info("  - skin_analysis_history")
        logger.info("  - coco_dataset_metadata")
        
    except Exception as e:
        logger.error(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
