"""
Create all tables on startup if they don't exist.
Safe to call repeatedly — CREATE TABLE IF NOT EXISTS semantics via SQLAlchemy metadata.
"""
import logging

logger = logging.getLogger("black.db.migrate")


def run_migrations() -> bool:
    """
    Returns True if migrations ran, False if DB is not configured.
    Called from app lifespan in main.py.
    """
    from app.db.session import engine, is_available
    if not is_available() or engine is None:
        logger.info("DB not configured — skipping migrations, JSON stores active")
        return False

    from app.db.models import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("DB migrations complete — all tables ready")
        return True
    except Exception as exc:
        logger.error(f"DB migration failed: {exc}")
        return False
