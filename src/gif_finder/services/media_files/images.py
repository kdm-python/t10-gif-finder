from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ImageFacts:
    format: str
    mime_type: str | None
    width: int
    height: int
    frame_count: int
    has_animation: bool
    duration_ms: int | None


def _get_duration_ms(image: Image.Image, frame_count: int) -> int | None:
    """Sum per-frame durations when Pillow exposes them."""
    duration_ms = 0
    has_timing_data = False

    for frame_index in range(frame_count):
        image.seek(frame_index)
        frame_duration = image.info.get("duration")

        if frame_duration is not None:
            duration_ms += frame_duration
            has_timing_data = True

    return duration_ms if has_timing_data else None


def inspect_image(path: Path) -> ImageFacts:
    with Image.open(path) as image:
        frame_count = getattr(image, "n_frames", 1)

        return ImageFacts(
            format=image.format,
            mime_type=Image.MIME.get(image.format),
            width=image.width,
            height=image.height,
            frame_count=frame_count,
            has_animation=frame_count > 1,
            duration_ms=_get_duration_ms(image, frame_count),
        )
