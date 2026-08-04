"""SQLAlchemy database engine and session setup."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()

if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is missing. Add it to your .env file before using the database."
    )


class Base(DeclarativeBase):
    """Base class that all SQLAlchemy models inherit from."""


# The engine owns the database connection pool.
engine = create_engine(settings.database_url, pool_pre_ping=True)


# SessionLocal creates short-lived database sessions for API requests.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that gives each request its own database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
