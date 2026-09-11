"""Stream lookup and creation services."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from gif_finder.database.models import Media, Stream


class StreamService:
    """Encapsulate stream storage and lookup concerns."""

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Stream]:
        """Return every stream, ordered by date and id."""
        statement = select(Stream).order_by(Stream.stream_date, Stream.id)
        return list(self.session.exec(statement).all())

    def get_by_id(self, stream_id: int) -> Stream | None:
        """Fetch a stream by id."""
        return self.session.get(Stream, stream_id)

    def create(self, *, stream_date: date, description: str) -> Stream:
        """Create a new stream record."""
        stream = Stream(stream_date=stream_date, description=description.strip())
        self.session.add(stream)
        self.session.commit()
        self.session.refresh(stream)
        return stream

    def get_or_create(
        self, *, stream_date: date, description: str | None = None
    ) -> Stream:
        """Return an existing stream or create one if needed."""
        existing = self.session.exec(
            select(Stream).where(
                Stream.stream_date == stream_date,
                Stream.description == (description or "").strip(),
            )
        ).first()
        if existing is not None:
            return existing
        return self.create(stream_date=stream_date, description=description or "")

    def delete(self, stream_id: int) -> None:
        """Delete a stream, raising if it is still attached to media."""
        stream = self.session.get(Stream, stream_id)
        if stream is None:
            raise ValueError(f"Stream {stream_id} does not exist.")

        in_use = self.session.exec(
            select(Media).where(Media.stream_id == stream_id)
        ).first()
        if in_use is not None:
            raise ValueError(
                f"Stream {stream_id} is still attached to media and cannot be deleted."
            )

        self.session.delete(stream)
        self.session.commit()
