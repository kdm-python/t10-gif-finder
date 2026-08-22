import os

from sqlmodel import Session, SQLModel, create_engine

from gif_finder.database.models import (  # noqa: F401
    Emote,
    Media,
    MediaTag,
    Stream,
    Tag,
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/giffinder.db")

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
