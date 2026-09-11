"""Media lookup, listing and deletion services."""

from __future__ import annotations

from sqlmodel import Session, select

from gif_finder.database.models import Media, MediaTag, Tag
from gif_finder.services.storage import delete_stored_media


class MediaService:
    """Encapsulate media listing, lookup and deletion operations."""

    def __init__(self, session: Session):
        self.session = session

    def list(
        self,
        *,
        tag: str | None = None,
        author: str | None = None,
        stream_id: int | None = None,
    ) -> list[Media]:
        """Return media rows, optionally filtered by tag name, author or stream."""
        statement = select(Media)

        if tag is not None:
            statement = (
                statement.join(MediaTag, MediaTag.media_id == Media.id)
                .join(Tag, Tag.id == MediaTag.tag_id)
                .where(Tag.name == tag)
            )

        if author is not None:
            statement = statement.where(Media.author == author)

        if stream_id is not None:
            statement = statement.where(Media.stream_id == stream_id)

        statement = statement.order_by(Media.id)
        return list(self.session.exec(statement).all())

    def get_by_id(self, media_id: int) -> Media | None:
        """Fetch a media row by id."""
        return self.session.get(Media, media_id)

    def get_tags_for_media(self, media_ids: list[int]) -> dict[int, list[str]]:
        """Return a mapping of media id to its attached tag names."""
        if not media_ids:
            return {}

        rows = self.session.exec(
            select(MediaTag.media_id, Tag.name)
            .join(Tag, Tag.id == MediaTag.tag_id)
            .where(MediaTag.media_id.in_(media_ids))
        ).all()

        tags_by_media: dict[int, list[str]] = {media_id: [] for media_id in media_ids}
        for media_id, tag_name in rows:
            tags_by_media[media_id].append(tag_name)
        return tags_by_media

    def delete(self, media_id: int) -> None:
        """Delete a media row, its tag links, and its stored file."""
        media = self.session.get(Media, media_id)
        if media is None:
            raise ValueError(f"Media {media_id} does not exist.")

        media_tags = self.session.exec(
            select(MediaTag).where(MediaTag.media_id == media_id)
        ).all()
        for media_tag in media_tags:
            self.session.delete(media_tag)

        delete_stored_media(media.file_path)

        self.session.delete(media)
        self.session.commit()
