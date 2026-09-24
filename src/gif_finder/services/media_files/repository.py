"""PostgreSQL persistence operations for the media-files service."""

from __future__ import annotations

from collections.abc import Iterable

from loguru import logger
from sqlmodel import Session, select

from gif_finder.database.models import Emote, Media, MediaTag, Stream, Tag
from gif_finder.services.media_files.contracts import (
    MediaFileInfo,
    MediaImportRequest,
    StoredMedia,
)


class MediaRepositoryError(ValueError):
    """Raised when data cannot be persisted consistently."""


class MediaRepository:
    """Database-only operations for media, tags, emotes, and streams.

    Methods may flush to obtain generated IDs, but never commit. The calling
    service owns the transaction so an import remains all-or-nothing.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, media_id: int) -> Media | None:
        """Return a media record by primary key."""
        return self.session.get(Media, media_id)

    def get_by_content_hash(self, content_hash: str) -> Media | None:
        """Return the canonical record for a content hash, if it exists."""
        statement = select(Media).where(Media.content_hash == content_hash)
        return self.session.exec(statement).first()

    def create_media(
        self,
        *,
        info: MediaFileInfo,
        stored: StoredMedia,
        request: MediaImportRequest,
        emote_id: int | None = None,
    ) -> Media:
        """Create and flush a Media record without committing."""
        self._validate_persistable_info(info)
        self._validate_request(request)

        media = Media(
            content_hash=stored.content_hash,
            storage_key=stored.storage_key,
            original_filename=stored.original_filename,
            original_extension=self._extension(stored.original_filename),
            file_size_bytes=stored.file_size_bytes,
            media_kind=info.media_kind,
            format=self._canonical_format(info),
            mime_type=info.mime_type,
            width=info.width,
            height=info.height,
            duration_ms=info.duration_ms,
            frame_count=info.frame_count,
            frame_rate=info.frame_rate,
            has_animation=bool(info.has_animation),
            has_alpha=info.has_alpha,
            rotation_degrees=info.rotation_degrees,
            video_codec=info.video_codec,
            pixel_format=info.pixel_format,
            video_bitrate=info.video_bitrate,
            has_audio=info.has_audio,
            audio_codec=info.audio_codec,
            audio_channels=info.audio_channels,
            audio_sample_rate=info.audio_sample_rate,
            audio_bitrate=info.audio_bitrate,
            title=self._clean_optional(request.title),
            description=self._clean_optional(request.description),
            author=self._clean_optional(request.author),
            source_url=self._clean_optional(request.source_url),
            emote_id=emote_id,
            stream_id=request.stream_id,
            probe_data=info.probe_data or None,
            probe_version=info.probe_version,
        )
        self.session.add(media)
        self.session.flush()

        logger.debug("Created media row {} for hash {}", media.id, stored.content_hash)
        return media

    def get_stream(self, stream_id: int) -> Stream | None:
        """Return a stream record by primary key."""
        return self.session.get(Stream, stream_id)

    def get_emote(self, emote_id: int) -> Emote | None:
        """Return an emote record by primary key."""
        return self.session.get(Emote, emote_id)

    def find_or_create_tag(self, name: str) -> Tag:
        """Find or create one canonical, case-insensitive tag without committing."""
        cleaned_name = self.normalise_tag_name(name)
        existing = self.session.exec(
            select(Tag).where(Tag.name == cleaned_name)
        ).first()
        if existing is not None:
            return existing

        tag = Tag(name=cleaned_name)
        self.session.add(tag)
        self.session.flush()
        logger.debug("Created tag {!r}", cleaned_name)
        return tag

    def attach_tags(self, media: Media, tag_names: Iterable[str]) -> None:
        """Attach each unique tag to media without committing."""
        if media.id is None:
            raise MediaRepositoryError("Media must be flushed before attaching tags.")

        names = sorted({self.normalise_tag_name(name) for name in tag_names})
        if not names:
            raise MediaRepositoryError("At least one tag is required.")

        for name in names:
            tag = self.find_or_create_tag(name)
            if tag.id is None:  # pragma: no cover - flush above guarantees this
                raise MediaRepositoryError("Tag must be flushed before linking.")

            link = self.session.exec(
                select(MediaTag).where(
                    MediaTag.media_id == media.id,
                    MediaTag.tag_id == tag.id,
                )
            ).first()
            if link is None:
                self.session.add(MediaTag(media_id=media.id, tag_id=tag.id))

    def replace_tags(self, media: Media, tag_names: Iterable[str]) -> None:
        """Replace a media item's complete tag set without committing."""
        if media.id is None:
            raise MediaRepositoryError("Media must have an ID before replacing tags.")

        names = list(tag_names)
        if not names:
            raise MediaRepositoryError("At least one tag is required.")

        for link in self.session.exec(
            select(MediaTag).where(MediaTag.media_id == media.id)
        ).all():
            self.session.delete(link)
        self.session.flush()
        self.attach_tags(media, names)

    def find_or_create_emote(self, name: str) -> Emote:
        """Find or create an optional emote without committing."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise MediaRepositoryError("Emote name cannot be blank.")

        existing = self.session.exec(
            select(Emote).where(Emote.name == cleaned_name)
        ).first()
        if existing is not None:
            return existing

        emote = Emote(name=cleaned_name)
        self.session.add(emote)
        self.session.flush()
        logger.debug("Created emote {!r}", cleaned_name)
        return emote

    def list_media(
        self,
        *,
        tag: str | None = None,
        author: str | None = None,
        emote_name: str | None = None,
        stream_id: int | None = None,
        media_kind: str | None = None,
        media_format: str | None = None,
    ) -> list[Media]:
        """List media rows using catalogue filters."""
        statement = select(Media)

        if tag is not None:
            statement = (
                statement.join(MediaTag, MediaTag.media_id == Media.id)
                .join(Tag, Tag.id == MediaTag.tag_id)
                .where(Tag.name == self.normalise_tag_name(tag))
            )
        if author is not None:
            statement = statement.where(Media.author == author.strip())
        if emote_name is not None:
            statement = (
                statement.join(Emote, Emote.id == Media.emote_id)
                .where(Emote.name == emote_name.strip())
            )
        if stream_id is not None:
            statement = statement.where(Media.stream_id == stream_id)
        if media_kind is not None:
            statement = statement.where(Media.media_kind == media_kind.strip().lower())
        if media_format is not None:
            statement = statement.where(Media.format == media_format.strip().upper())

        return list(self.session.exec(statement.order_by(Media.id)).all())

    def get_tags_for_media(self, media_ids: Iterable[int]) -> dict[int, list[str]]:
        """Return tag names keyed by media ID."""
        ids = list(media_ids)
        if not ids:
            return {}

        rows = self.session.exec(
            select(MediaTag.media_id, Tag.name)
            .join(Tag, Tag.id == MediaTag.tag_id)
            .where(MediaTag.media_id.in_(ids))
            .order_by(MediaTag.media_id, Tag.name)
        ).all()
        tags_by_media: dict[int, list[str]] = {media_id: [] for media_id in ids}
        for media_id, name in rows:
            tags_by_media[media_id].append(name)
        return tags_by_media

    def delete_media(self, media: Media) -> None:
        """Delete one media row and its tag links without committing."""
        if media.id is None:
            raise MediaRepositoryError("Media must have an ID before deletion.")

        for link in self.session.exec(
            select(MediaTag).where(MediaTag.media_id == media.id)
        ).all():
            self.session.delete(link)

        # Flush link deletes first: the PostgreSQL foreign key does not permit
        # deleting Media while a MediaTag still references it.
        self.session.flush()
        self.session.delete(media)

    @staticmethod
    def normalise_tag_name(name: str) -> str:
        """Return the canonical tag form used for uniqueness and search."""
        cleaned_name = name.strip().casefold()
        if not cleaned_name:
            raise MediaRepositoryError("Tag name cannot be blank.")
        return cleaned_name

    @staticmethod
    def _validate_request(request: MediaImportRequest) -> None:
        if not request.tags or not any(tag.strip() for tag in request.tags):
            raise MediaRepositoryError("At least one tag is required.")

    @staticmethod
    def _validate_persistable_info(info: MediaFileInfo) -> None:
        required_values = {
            "mime_type": info.mime_type,
            "width": info.width,
            "height": info.height,
        }
        missing = [name for name, value in required_values.items() if value is None]
        if missing:
            raise MediaRepositoryError(
                "Cannot persist media with missing required metadata: "
                + ", ".join(missing)
            )

    @staticmethod
    def _canonical_format(info: MediaFileInfo) -> str:
        if info.mime_type and "/" in info.mime_type:
            return info.mime_type.split("/", maxsplit=1)[1].upper()
        if info.container_format:
            return info.container_format.split(",", maxsplit=1)[0].upper()
        raise MediaRepositoryError("Cannot determine a media format.")

    @staticmethod
    def _extension(filename: str) -> str | None:
        suffix = filename.rsplit(".", maxsplit=1)
        if len(suffix) == 1:
            return None
        return f".{suffix[-1].lower()}"

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None
