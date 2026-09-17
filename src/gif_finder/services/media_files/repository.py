"""Database persistence for the media-files service."""

from __future__ import annotations

from sqlmodel import Session, select

from gif_finder.database.models import Media, MediaTag, Tag
from gif_finder.services.media_files.contracts import MediaFileInfo
from gif_finder.services.media_files.storage import StoredMedia


class MediaRepositoryError(ValueError):
    """Raised when inspected data cannot be persisted as a Media row."""


class MediaRepository:
    """Database-only operations for media and media-tag records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, media_id: int) -> Media | None:
        """Return one media row by its primary key."""
        return self.session.get(Media, media_id)

    def get_by_hash(self, content_hash: str) -> Media | None:
        """Return the first media row with this content hash."""
        statement = select(Media).where(Media.file_hash == content_hash)
        return self.session.exec(statement).first()

    # TODO: Implement handling of tags and emote here and adapt to new database
    def create(
        self,
        *,
        info: MediaFileInfo,
        stored: StoredMedia,
        author: str | None = None,
        stream_id: int | None = None,
        tags: list[str] | None = None,
        emote: str | None = None,
    ) -> Media:
        """Create and flush one Media row, without committing."""
        self._validate_persistable_info(info)

        # TODO: Adapt database fields to new schema, including tags and emote.
        media = Media(
            # Temporary compatibility: this existing DB column now holds a
            # relative storage key, not an absolute file path.
            file_path=stored.storage_key,
            original_filename=stored.original_filename,
            format=self._canonical_format(info),
            mime_type=info.mime_type,
            file_size=stored.file_size_bytes,
            width=info.width,
            height=info.height,
            frame_count=info.frame_count,
            frame_rate=info.frame_rate,
            duration_ms=info.duration_ms,
            has_animation=bool(info.has_animation),
            author=author,
            stream_id=stream_id,
            file_hash=stored.content_hash,
        )

        self.session.add(media)
        self.session.flush()

        return media

    def find_or_create_tag(self, name: str) -> Tag:
        """Find or create a tag, without committing."""
        cleaned_name = name.strip()

        if not cleaned_name:
            raise MediaRepositoryError("Tag name cannot be blank.")

        existing = self.session.exec(
            select(Tag).where(Tag.name == cleaned_name)
        ).first()

        if existing is not None:
            return existing

        tag = Tag(name=cleaned_name)
        self.session.add(tag)
        self.session.flush()

        return tag

    def attach_tags(self, media: Media, tag_names: list[str]) -> None:
        """Attach unique tag names to media, without committing."""
        if media.id is None:
            raise MediaRepositoryError("Media must be flushed before attaching tags.")

        unique_names = {name.strip() for name in tag_names if name.strip()}

        for tag_name in unique_names:
            tag = self.find_or_create_tag(tag_name)

            if tag.id is None:
                raise MediaRepositoryError("Tag must be flushed before linking.")

            existing_link = self.session.exec(
                select(MediaTag).where(
                    MediaTag.media_id == media.id,
                    MediaTag.tag_id == tag.id,
                )
            ).first()

            if existing_link is None:
                self.session.add(MediaTag(media_id=media.id, tag_id=tag.id))

    def list(
        self,
        *,
        tag: str | None = None,
        author: str | None = None,
        stream_id: int | None = None,
    ) -> list[Media]:
        """List media records with optional catalogue filters."""
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

        return list(self.session.exec(statement.order_by(Media.id)).all())

    def get_tags_for_media(self, media_ids: list[int]) -> dict[int, list[str]]:
        """Return tag names keyed by media ID."""
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

    def delete(self, media: Media) -> None:
        """Delete a media row and its tag links, without committing."""
        if media.id is None:
            raise MediaRepositoryError("Media must have an ID before deletion.")

        links = self.session.exec(
            select(MediaTag).where(MediaTag.media_id == media.id)
        ).all()

        for link in links:
            self.session.delete(link)

        self.session.delete(media)

    @staticmethod
    def _validate_persistable_info(info: MediaFileInfo) -> None:
        """Ensure values required by the current Media database schema exist."""
        required_values = {
            "container_format": info.container_format,
            "mime_type": info.mime_type,
            "width": info.width,
            "height": info.height,
            "frame_count": info.frame_count,
        }

        missing = [
            field_name for field_name, value in required_values.items() if value is None
        ]

        if missing:
            fields = ", ".join(missing)
            raise MediaRepositoryError(
                f"Cannot persist media with missing required metadata: {fields}"
            )

    @staticmethod
    def _canonical_format(info: MediaFileInfo) -> str:
        """Produce a stable application format label for the current DB column."""
        if info.mime_type is not None and "/" in info.mime_type:
            return info.mime_type.split("/", maxsplit=1)[1].upper()

        if info.container_format is not None:
            return info.container_format.upper()

        raise MediaRepositoryError("Cannot determine a media format.")
