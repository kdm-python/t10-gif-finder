"""Media preparation service."""

from __future__ import annotations

from pathlib import Path

from gif_finder.database.models import Media
from gif_finder.services.media_processor import inspect_media
from gif_finder.services.storage import store_media

FRAME_RATE_DEFAULT = 24.0


def prepare_media(
    media_file: Path,
    author: str | None = None,
    stream_id: int | None = None,
    *,
    destination_root: Path | str | None = None,
    frame_rate: float | None = None,
) -> Media:
    """Inspect, persist, and return a Media row suitable for database insertion."""
    source = Path(media_file).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Media file not found: {source}")

    metadata = inspect_media(
        source, frame_rate=FRAME_RATE_DEFAULT if frame_rate is None else frame_rate
    )

    # Check suffix and use supplied frame rate if .webp file
    if source.suffix.lower() == ".webp" and frame_rate is not None:
        metadata.frame_rate = frame_rate

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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run src/gif_finder/services/media.py <path>")
        raise SystemExit(1)

    path = Path(sys.argv[1])

    media = prepare_media(path, frame_rate=24)

    print(media)
