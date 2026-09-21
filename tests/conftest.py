from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, create_engine

from gif_finder.database.models import Emote, Media, MediaTag, Stream, Tag

load_dotenv()


def _test_database_url() -> str:
    database_url = os.getenv("GIFFINDER_TEST_DATABASE_URL")

    if not database_url:
        logger.error("GIFFINDER_TEST_DATABASE_URL is not configured.")
        pytest.exit("Database tests require GIFFINDER_TEST_DATABASE_URL.")

    database_name = make_url(database_url).database
    if database_name is None or not database_name.endswith("_test"):
        logger.error("Refusing database tests against {!r}.", database_name)
        pytest.exit("Test database name must end with '_test'.")

    return database_url


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(_test_database_url())

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        logger.error("Could not connect to giffinder_test: {}", exc)
        pytest.exit(
            "giffinder_test must already exist and be reachable before DB tests."
        )

    return engine


def _truncate_database(engine) -> None:
    table_names = [
        MediaTag.__table__.name,
        Media.__table__.name,
        Tag.__table__.name,
        Emote.__table__.name,
        Stream.__table__.name,
    ]
    tables = ", ".join(table_names)

    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


def _require_schema(engine) -> None:
    required_tables = [
        MediaTag.__table__.name,
        Media.__table__.name,
        Tag.__table__.name,
        Emote.__table__.name,
        Stream.__table__.name,
    ]
    present_tables = set(inspect(engine).get_table_names())
    missing_tables = sorted(set(required_tables) - present_tables)

    if missing_tables:
        logger.error(
            "giffinder_test is reachable but lacks required tables: {}",
            ", ".join(missing_tables),
        )
        pytest.exit("Apply the GIF Finder schema before running database tests.")


@pytest.fixture
def db_session(test_engine):
    _require_schema(test_engine)
    _truncate_database(test_engine)

    with Session(test_engine) as session:
        yield session

    _truncate_database(test_engine)
