import os

from sqlmodel import Session, SQLModel, create_engine

from .models import Emote, EmoteMedia, Media, MediaTag, Stream, Tag  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///giffinder.db")

engine = create_engine(
    DATABASE_URL,
    echo=True,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
