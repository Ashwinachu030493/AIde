import logging
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text

from server.shared.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add huggingface_api_key to user_settings table"""
    db = SessionLocal()
    try:
        logger.info("Checking for huggingface_api_key column...")

        # Check if column exists
        result = db.execute(text("PRAGMA table_info(user_settings)"))
        columns = [row.name for row in result]

        if "huggingface_api_key" not in columns:
            logger.info("Adding huggingface_api_key column...")
            db.execute(text("ALTER TABLE user_settings ADD COLUMN huggingface_api_key TEXT"))
            db.commit()
            logger.info("Migration successful.")
        else:
            logger.info("Column already exists.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
