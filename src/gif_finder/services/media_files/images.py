from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ImageFacts:
    """Technical metadata extracted from an image file."""

    format: str
    mime_type: str | None
    width: int
    height: int
    frame_count: int
    has_animation: bool
    has_alpha: bool | None
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
    """Inspect an image file and return its technical metadata."""
    with Image.open(path) as image:
        frame_count = getattr(image, "n_frames", 1)

        return ImageFacts(
            format=image.format,
            mime_type=Image.MIME.get(image.format),
            width=image.width,
            height=image.height,
            frame_count=frame_count,
            has_animation=frame_count > 1,
            has_alpha=_has_alpha_channel(image),
            duration_ms=_get_duration_ms(image, frame_count),
        )


def _has_alpha_channel(image: Image.Image) -> bool:
    """Return whether Pillow reports an alpha channel or transparency metadata."""
    return "A" in image.getbands() or "transparency" in image.info
