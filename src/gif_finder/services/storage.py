"""Media storage helpers."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

DEFAULT_MEDIA_ROOT = Path(__file__).resolve().parents[3] / "media"


@dataclass(frozen=True)
class StoredMedia:
    file_path: str
    file_hash: str
    original_filename: str
    destination_root: str


def store_media(
    media_file: Path,
    *,
    destination_root: Path | str | None = None,
) -> StoredMedia:
    """Copy a source file into the project media store and return its storage metadata."""
    source = Path(media_file).expanduser().resolve()

    logger.info("SOURCE: {}", source)
    logger.info("EXTENSION: {}", source.suffix)
    logger.info("DESTINATION: {}", destination_root)

    if not source.exists():
        raise FileNotFoundError(f"Media file does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Media path is not a file: {source}")

    root = (
        Path(destination_root).expanduser().resolve()
        if destination_root
        else DEFAULT_MEDIA_ROOT
    )

    root.mkdir(parents=True, exist_ok=True)

    file_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    extension = source.suffix.lower() or ".bin"
    storage_dir = root / file_hash[:2]
    storage_dir.mkdir(parents=True, exist_ok=True)

    destination = storage_dir / f"{file_hash}{extension}"
    if not destination.exists():
        shutil.copy2(source, destination)
        logger.info("Stored media file {} -> {}", source, destination)
    else:
        logger.info("Media file already exists at {}", destination)

    return StoredMedia(
        file_path=str(destination.resolve()),
        file_hash=file_hash,
        original_filename=source.name,
        destination_root=str(root.resolve()),
    )


def delete_stored_media(file_path: Path | str) -> None:
    """Remove a previously stored media file, tolerating an already-missing file."""
    path = Path(file_path)
    try:
        path.unlink()
        logger.info("Deleted stored media file {}", path)
    except FileNotFoundError:
        logger.warning("Stored media file already missing: {}", path)
