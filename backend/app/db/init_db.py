"""Database table creation helper."""

from app.db.session import Base, engine

# Importing the model modules registers their tables with SQLAlchemy metadata.
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.user import User  # noqa: F401


def create_tables() -> None:
    """Create all database tables that do not already exist."""

    Base.metadata.create_all(bind=engine)
