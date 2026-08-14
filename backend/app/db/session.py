"""
Database session — SQLAlchemy + Postgres.

DATABASE_URL in .env controls the connection.
When not set, the DB layer is disabled and all stores fall back to JSON files.
This keeps Mr. Black runnable locally without Postgres.
"""
import os
from contextlib import contextmanager
from typing import Generator

_DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = None
SessionLocal = None
_db_available = False


def _init():
    global engine, SessionLocal, _db_available
    if not _DATABASE_URL:
        return
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(
            _DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 5},
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _db_available = True
    except Exception as exc:
        import logging
        logging.getLogger("black.db").warning(f"DB init skipped: {exc}")


_init()


def is_available() -> bool:
    return _db_available


@contextmanager
def get_session() -> Generator:
    if not _db_available or SessionLocal is None:
        raise RuntimeError("Database not configured")
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
