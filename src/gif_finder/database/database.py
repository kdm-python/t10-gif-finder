from contextlib import contextmanager

from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

from gif_finder.config import settings
from gif_finder.database.models import (  # noqa: F401
    Emote,
    Media,
    MediaTag,
    Stream,
    Tag,
)

engine = create_engine(
    settings.active_database_url,
    echo=False,
)


class DatabaseUnavailableError(RuntimeError):
    """Raised when the configured PostgreSQL database cannot be reached."""


def verify_database_connection() -> None:
    """Verify the configured database exists before running application work."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error(
            "Cannot connect to the {} database. Ensure it exists and the configured "
            "credentials are valid: {}",
            settings.giffinder_env,
            exc,
        )
        raise DatabaseUnavailableError(
            "Configured GIF Finder database is unavailable."
        ) from exc


def create_db_and_tables():
    """Create missing tables in the configured, already-existing database."""
    verify_database_connection()
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    verify_database_connection()
    with Session(engine) as session:
        yield session
