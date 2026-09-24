"""Application workflows for inspecting and cataloguing media files."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from sqlmodel import Session

from gif_finder.database.models import Media
from gif_finder.services.media_files.contracts import (
    MediaFileInfo,
    MediaImportRequest,
    MediaUpdateRequest,
    StoredMedia,
)
from gif_finder.services.media_files.inspector import inspect_media_file
from gif_finder.services.media_files.repository import MediaRepository
from gif_finder.services.media_files.storage import MediaStorage


class MediaFilesServiceError(RuntimeError):
    """Raised when a media-files workflow cannot complete."""


class MediaFilesService:
    """Coordinate inspection, content-addressed storage, and persistence."""

    def __init__(self, session: Session, storage: MediaStorage) -> None:
        self.session = session
        self.storage = storage
        self.repository = MediaRepository(session)

    @classmethod
    def from_settings(cls, session: Session) -> MediaFilesService:
        """Build the service using the media root for the active environment."""
        from gif_finder.config import settings

        return cls(session, MediaStorage(settings.active_media_root))

    def inspect(self, source_path: Path | str) -> MediaFileInfo:
        """Inspect a source file without storing or cataloguing it."""
        logger.info("Inspecting media file {}", source_path)
        return inspect_media_file(source_path)

    def import_media(self, request: MediaImportRequest) -> Media:
        """Import media atomically across the database and file store."""
        request = self._normalise_request(request)
        logger.info("Importing media {} with tags {}", request.source_path, request.tags)

        stored: StoredMedia | None = None
        try:
            info = self.inspect(request.source_path)
            stored = self.storage.store(
                request.source_path,
                original_filename=request.original_filename,
            )

            self._validate_stream(request.stream_id)
            emote_id = self._resolve_emote_id(request.emote_name)
            existing = self.repository.get_by_content_hash(stored.content_hash)

            if existing is not None:
                logger.info(
                    "Media hash already catalogued as row {}; merging catalogue data.",
                    existing.id,
                )
                self.repository.attach_tags(existing, request.tags)
                self._merge_user_metadata(existing, request, emote_id)
                self.session.commit()
                self.session.refresh(existing)
                return existing

            media = self.repository.create_media(
                info=info,
                stored=stored,
                request=request,
                emote_id=emote_id,
            )
            self.repository.attach_tags(media, request.tags)
            self.session.commit()
            self.session.refresh(media)
            logger.success("Imported media row {}", media.id)
            return media
        except Exception:
            self.session.rollback()
            self._clean_failed_storage(stored)
            logger.exception("Media import failed for {}", request.source_path)
            raise

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
        """List catalogue rows using optional filters."""
        return self.repository.list_media(
            tag=tag,
            author=author,
            emote_name=emote_name,
            stream_id=stream_id,
            media_kind=media_kind,
            media_format=media_format,
        )

    def get_tags_for_media(self, media_ids: list[int]) -> dict[int, list[str]]:
        """Return tags for a group of catalogue rows."""
        return self.repository.get_tags_for_media(media_ids)

    def get_media(self, media_id: int) -> Media | None:
        """Return one media record by ID."""
        return self.repository.get_by_id(media_id)

    def update_media(self, media_id: int, request: MediaUpdateRequest) -> Media:
        """Update mutable catalogue fields while preserving inspected facts."""
        media = self.repository.get_by_id(media_id)
        if media is None:
            raise MediaFilesServiceError(f"Media {media_id} does not exist.")

        if "stream_id" in request.provided_fields:
            self._validate_stream(request.stream_id)
            media.stream_id = request.stream_id
        if "emote_id" in request.provided_fields:
            if (
                request.emote_id is not None
                and self.repository.get_emote(request.emote_id) is None
            ):
                raise MediaFilesServiceError(
                    f"Emote {request.emote_id} does not exist."
                )
            media.emote_id = request.emote_id
        if "tags" in request.provided_fields:
            if not request.tags:
                raise MediaFilesServiceError("At least one tag is required for media.")
            self.repository.replace_tags(media, request.tags)

        for field_name in {"title", "description", "author", "source_url"} & request.provided_fields:
            setattr(media, field_name, self._optional_text(getattr(request, field_name)))

        media.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(media)
        logger.info("Updated media row {} fields={}", media.id, sorted(request.provided_fields))
        return media

    def resolve_media_file(self, media_id: int) -> tuple[Media, Path]:
        """Resolve a stored media object for safe HTTP delivery."""
        media = self.repository.get_by_id(media_id)
        if media is None:
            raise MediaFilesServiceError(f"Media {media_id} does not exist.")
        path = self.storage.resolve(media.storage_key)
        if not path.is_file():
            raise MediaFilesServiceError(f"Stored file for media {media_id} is missing.")
        return media, path

    def delete_media(self, media_id: int) -> None:
        """Delete a media row and then remove its unique stored object."""
        media = self.repository.get_by_id(media_id)
        if media is None:
            raise MediaFilesServiceError(f"Media {media_id} does not exist.")

        storage_key = media.storage_key
        self.repository.delete_media(media)
        self.session.commit()

        try:
            self.storage.delete(storage_key)
        except Exception:
            logger.exception(
                "Deleted media row {} but could not remove stored object {}. "
                "It can be cleaned up by a later storage audit.",
                media_id,
                storage_key,
            )
            raise

        logger.success("Deleted media row {} and stored object", media_id)

    def _validate_stream(self, stream_id: int | None) -> None:
        if stream_id is not None and self.repository.get_stream(stream_id) is None:
            raise MediaFilesServiceError(f"Stream {stream_id} does not exist.")

    def _resolve_emote_id(self, emote_name: str | None) -> int | None:
        if emote_name is None:
            return None

        emote = self.repository.find_or_create_emote(emote_name)
        if emote.id is None:  # pragma: no cover - repository flushes emotes
            raise MediaFilesServiceError("Emote did not receive a database ID.")
        return emote.id

    @staticmethod
    def _merge_user_metadata(
        media: Media,
        request: MediaImportRequest,
        emote_id: int | None,
    ) -> None:
        """Fill missing optional user fields on a duplicate-content import."""
        if media.author is None:
            media.author = request.author
        if media.title is None:
            media.title = request.title
        if media.description is None:
            media.description = request.description
        if media.source_url is None:
            media.source_url = request.source_url
        if media.emote_id is None:
            media.emote_id = emote_id

    def _clean_failed_storage(self, stored: StoredMedia | None) -> None:
        """Remove a new stored object unless a committed media row references it."""
        if stored is None or not stored.was_created:
            return

        try:
            if self.repository.get_by_content_hash(stored.content_hash) is None:
                self.storage.delete(stored.storage_key)
        except Exception:
            logger.exception(
                "Could not clean up stored object {} after failed import.",
                stored.storage_key,
            )

    @staticmethod
    def _normalise_request(request: MediaImportRequest) -> MediaImportRequest:
        tags = list(
            dict.fromkeys(tag.strip().casefold() for tag in request.tags if tag.strip())
        )
        if not tags:
            raise MediaFilesServiceError("At least one tag is required to import media.")

        return replace(
            request,
            source_path=Path(request.source_path).expanduser(),
            tags=tags,
            author=MediaFilesService._optional_text(request.author),
            emote_name=MediaFilesService._optional_text(request.emote_name),
            title=MediaFilesService._optional_text(request.title),
            description=MediaFilesService._optional_text(request.description),
            source_url=MediaFilesService._optional_text(request.source_url),
        )

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        return value.strip() or None if value is not None else None
