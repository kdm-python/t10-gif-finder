"""Content-addressed filesystem storage for imported media."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from loguru import logger

from gif_finder.services.media_files.contracts import StoredMedia


class MediaStorageError(ValueError):
    """Raised for unsafe or invalid storage operations."""


class MediaStorage:
    """Store and retrieve media under a configured secure root."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()

    def store(
        self, source: Path | str, *, original_filename: str | None = None
    ) -> StoredMedia:
        """Hash and copy a source file, reusing an existing identical object."""
        source_path = Path(source).expanduser().resolve()
        self._validate_source(source_path)
        display_filename = self._display_filename(original_filename, source_path.name)
        logger.info("Staging media file for storage: {}", source_path)
        staged_path, content_hash, file_size_bytes = self._stage_copy_and_hash(
            source_path, self.root
        )
        storage_key = self._storage_key_for_hash(content_hash)
        destination = self.resolve(storage_key)

        if destination.exists():
            staged_path.unlink(missing_ok=True)
            logger.info("Reused stored media object {}", storage_key)
            return StoredMedia(
                content_hash=content_hash,
                storage_key=storage_key,
                original_filename=display_filename,
                file_size_bytes=file_size_bytes,
                was_created=False,
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_path, destination)
        logger.info("Stored media object at {}", storage_key)

        return StoredMedia(
            content_hash=content_hash,
            storage_key=storage_key,
            original_filename=display_filename,
            file_size_bytes=file_size_bytes,
            was_created=True,
        )

    def resolve(self, storage_key: str) -> Path:
        """Resolve a DB storage key safely underneath this storage root."""
        candidate = (self.root / storage_key).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise MediaStorageError(
                f"Storage key escapes the configured media root: {storage_key}"
            ) from exc

        return candidate

    def delete(self, storage_key: str) -> None:
        """Remove one stored object; service code must verify references first."""
        path = self.resolve(storage_key)

        try:
            path.unlink()
            logger.info("Deleted stored media object {}", storage_key)
        except FileNotFoundError:
            logger.warning("Stored media object was already absent: {}", storage_key)

    @staticmethod
    def _validate_source(source: Path) -> None:
        if not source.exists():
            raise FileNotFoundError(f"Media file does not exist: {source}")

        if not source.is_file():
            raise MediaStorageError(f"Media path is not a file: {source}")

    @staticmethod
    def _display_filename(value: str | None, fallback: str) -> str:
        """Keep only a safe filename for display; never retain a client path."""
        if value is None:
            return fallback

        filename = Path(value.replace("\\", "/")).name.strip()
        if not filename or filename in {".", ".."} or "\x00" in filename:
            return fallback
        return filename

    @staticmethod
    def _storage_key_for_hash(content_hash: str) -> str:
        return f"{content_hash[:2]}/{content_hash}"

    @staticmethod
    def _stage_copy_and_hash(source: Path, root: Path) -> tuple[Path, str, int]:
        """Copy and hash source once into a temporary file under the media root."""
        staging_root = root / ".staging"
        staging_root.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256()
        file_size_bytes = 0

        staged_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=staging_root,
                delete=False,
            ) as staged_file:
                staged_path = Path(staged_file.name)

                with source.open("rb") as source_file:
                    while chunk := source_file.read(1024 * 1024):
                        digest.update(chunk)
                        staged_file.write(chunk)
                        file_size_bytes += len(chunk)
        except Exception:
            if staged_path is not None:
                staged_path.unlink(missing_ok=True)
            raise

        if staged_path is None:  # pragma: no cover - defensive type narrowing
            raise MediaStorageError("Unable to create a staged media file.")

        return staged_path, digest.hexdigest(), file_size_bytes
