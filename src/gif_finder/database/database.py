from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from gif_finder.config import settings
from gif_finder.database.models import (  # noqa: F401
    Emote,
    Media,
    MediaTag,
    Stream,
    Tag,
)

DATABASE_URL = settings.postgres_url

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """Provide a transactional scope around a series of operations."""
    with Session(engine) as session:
        yield session
