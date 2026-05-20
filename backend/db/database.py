"""Database engine, session factory, and FK enforcement."""

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _resolve_database_url() -> str:
    """Get DATABASE_URL from env or default to local SQLite file."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    db_path = Path(__file__).parent.parent / "rinnegan.db"
    return f"sqlite:///{db_path}"


DATABASE_URL = _resolve_database_url()

# check_same_thread=False is required for FastAPI which uses multiple threads.
# pool_pre_ping ensures broken connections are detected before use.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(Engine, "connect")
def _enable_sqlite_fk(dbapi_conn, _):
    """Enable foreign key enforcement on SQLite (off by default).

    Without this, ondelete= clauses are silently ignored.
    """
    if hasattr(dbapi_conn, "execute"):
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            # WAL mode allows concurrent reads during writes (better for our use case)
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
