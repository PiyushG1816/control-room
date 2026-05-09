"""Database connection and SQLAlchemy session plumbing for Control Room."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


def _get_database_url() -> str:
    """Return the database URL from the environment or raise if unset."""
    url = os.environ.get("CONTROLROOM_DATABASE_URL")
    if not url:
        raise ValueError("CONTROLROOM_DATABASE_URL environment variable is not set.")
    return url


engine = create_engine(_get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and guarantee it is closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
