import sys
from pathlib import Path

from PIL import Image

from gif_finder.database.models import MediaMetadata


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
        elif format in ("WEBP", "AVIF"):
            if frame_rate is None:
                raise ValueError(
                    f"Frame rate must be provided for {format} media inspection."
                )
            frame_rate, duration_ms = _get_timing_from_frame_rate(
                frame_count,
                frame_rate,
            )
        else:
            raise ValueError(
                f"Unsupported media format: {format}. "
                "Only GIF, WEBP and AVIF are supported."
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
