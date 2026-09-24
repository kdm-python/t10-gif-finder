"""Reusable FastAPI dependencies."""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session

from gif_finder.database.database import get_session


def get_db_session() -> Generator[Session, None, None]:
    """Yield one database session for the lifetime of an HTTP request."""
    with get_session() as session:
        yield session
