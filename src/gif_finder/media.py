import math
from pathlib import Path
import sys

from PIL import Image

from gif_finder.models import MediaMetadata


def _convert_file_size(size_bytes: int) -> str:
    """Convert file size in bytes to a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = math.floor(math.log(size_bytes, 1024))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def _get_gif_timing(
    image: Image.Image,
    frame_count: int,
) -> tuple[float | None, int | None]:
    """Return frame rate and total duration for an animated GIF."""
    duration_ms = 0

    for frame in range(frame_count):
        image.seek(frame)
        duration_ms += image.info.get("duration", 0)

    if duration_ms <= 0:
        return None, None

    frame_rate = frame_count / (duration_ms / 1000)

    return frame_rate, duration_ms


def _get_timing_from_frame_rate(
    frame_count: int,
    frame_rate: float,
) -> tuple[float, int]:
    """Calculate duration from frame count and frame rate."""
    duration_ms = round(frame_count / frame_rate * 1000)

    return frame_rate, duration_ms


def inspect_media(
    path: Path,
    *,
    frame_rate: float | None = None,
) -> MediaMetadata:
    """Inspect an image/media file and return its metadata."""
    with Image.open(path) as image:
        format = image.format
        mime_type = Image.MIME[format]
        width, height = image.size
        file_size = path.stat().st_size
        frame_count = getattr(image, "n_frames", 1)
        has_animation = frame_count > 1

        duration_ms = None

        if format == "GIF":
            frame_rate, duration_ms = _get_gif_timing(
                image,
                frame_count,
            )
        elif frame_rate is not None:
            frame_rate, duration_ms = _get_timing_from_frame_rate(
                frame_count,
                frame_rate,
            )

        return MediaMetadata(
            format=format,
            mime_type=mime_type,
            width=width,
            height=height,
            file_size=file_size,
            frame_count=frame_count,
            frame_rate=frame_rate,
            duration_ms=duration_ms,
            has_animation=has_animation,
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: uv run src/gif_finder/media.py <path>")
        raise SystemExit(1)

    path = Path(sys.argv[1])

    metadata = inspect_media(path, frame_rate=24)

    print(metadata)
