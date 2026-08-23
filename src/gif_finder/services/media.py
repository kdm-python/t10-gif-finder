"""Media preparation service."""

from __future__ import annotations

from pathlib import Path

from gif_finder.database.models import Media
from gif_finder.services.media_processor import inspect_media
from gif_finder.services.storage import store_media


def prepare_media(
    media_file: Path,
    author: str | None = None,
    stream_id: int | None = None,
    *,
    destination_root: Path | str | None = None,
) -> Media:
    """Inspect, persist, and return a Media row suitable for database insertion."""
    source = Path(media_file).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Media file not found: {source}")

    metadata = inspect_media(source)
    stored = store_media(source, destination_root=destination_root)

    return Media(
        file_path=stored.file_path,
        original_filename=stored.original_filename,
        format=metadata.format,
        mime_type=metadata.mime_type,
        file_size=metadata.file_size,
        width=metadata.width,
        height=metadata.height,
        frame_count=metadata.frame_count,
        frame_rate=metadata.frame_rate,
        duration_ms=metadata.duration_ms,
        has_animation=metadata.has_animation,
        author=author,
        stream_id=stream_id,
        file_hash=stored.file_hash,
    )
