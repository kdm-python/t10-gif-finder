"""Content-addressed filesystem storage for imported media."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


class MediaStorageError(ValueError):
    """Raised for unsafe or invalid storage operations."""


@dataclass(frozen=True)
class StoredMedia:
    """Reference to one object in the content-addressed media store."""

    content_hash: str
    storage_key: str
    original_filename: str
    file_size_bytes: int
    was_created: bool


class MediaStorage:
    """Store and retrieve media under a configured secure root."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).expanduser().resolve()

    def store(self, source: Path | str) -> StoredMedia:
        """Hash and copy a source file, reusing an existing identical object."""
        source_path = Path(source).expanduser().resolve()
        self._validate_source(source_path)

        content_hash, file_size_bytes = self._hash_file(source_path)
        storage_key = self._storage_key_for_hash(content_hash)
        destination = self.resolve(storage_key)

        if destination.exists():
            return StoredMedia(
                content_hash=content_hash,
                storage_key=storage_key,
                original_filename=source_path.name,
                file_size_bytes=file_size_bytes,
                was_created=False,
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        self._copy_atomically(source_path, destination)

        return StoredMedia(
            content_hash=content_hash,
            storage_key=storage_key,
            original_filename=source_path.name,
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
        except FileNotFoundError:
            pass

    @staticmethod
    def _validate_source(source: Path) -> None:
        if not source.exists():
            raise FileNotFoundError(f"Media file does not exist: {source}")

        if not source.is_file():
            raise MediaStorageError(f"Media path is not a file: {source}")

    @staticmethod
    def _hash_file(source: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        file_size_bytes = 0

        with source.open("rb") as media_file:
            while chunk := media_file.read(1024 * 1024):
                digest.update(chunk)
                file_size_bytes += len(chunk)

        return digest.hexdigest(), file_size_bytes

    @staticmethod
    def _storage_key_for_hash(content_hash: str) -> str:
        return f"{content_hash[:2]}/{content_hash}"

    @staticmethod
    def _copy_atomically(source: Path, destination: Path) -> None:
        """Copy to a temporary sibling, then atomically put it in place."""
        temporary_path: Path | None = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

                with source.open("rb") as source_file:
                    shutil.copyfileobj(source_file, temporary_file)

            os.replace(temporary_path, destination)
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
