"""High-level inspection for supported media files.

Combines universal ffprobe metadata with Pillow image facts when available.
No database or storage work belongs here.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from PIL import UnidentifiedImageError

from gif_finder.services.media_files.contracts import MediaFileInfo
from gif_finder.services.media_files.ffprobe import run_ffprobe
from gif_finder.services.media_files.images import ImageFacts, inspect_image


class MediaInspectionError(ValueError):
    """Raised when a file cannot be treated as supported visual media."""


def inspect_media_file(path: Path | str) -> MediaFileInfo:
    """Inspect one GIF, WebP, MP4, or other ffprobe-supported visual file.

    ffprobe supplies container, codec, audio, and video-stream information.
    Pillow enriches image formats with dependable dimensions, frame count,
    duration, MIME type, and animation information.
    """
    source = Path(path).expanduser().resolve()

    if not source.exists():
        raise FileNotFoundError(f"Media file does not exist: {source}")

    if not source.is_file():
        raise MediaInspectionError(f"Media path is not a file: {source}")

    probe = run_ffprobe(source)
    video_stream = _first_stream_of_type(probe, "video")

    if video_stream is None:
        raise MediaInspectionError(f"No video stream found in: {source.name}")

    image_facts = try_inspect_image(source)
    audio_stream = _first_stream_of_type(probe, "audio")

    return MediaFileInfo(
        source_path=source,
        file_size_bytes=source.stat().st_size,
        container_format=_optional_str(probe.get("format", {}).get("format_name")),
        mime_type=_mime_type(source, image_facts),
        width=_preferred_int(
            image_facts.width if image_facts else None,
            video_stream.get("width"),
        ),
        height=_preferred_int(
            image_facts.height if image_facts else None,
            video_stream.get("height"),
        ),
        frame_count=_preferred_int(
            image_facts.frame_count if image_facts else None,
            video_stream.get("nb_frames"),
        ),
        frame_rate=_frame_rate(video_stream),
        duration_ms=_duration_ms(probe, video_stream, image_facts),
        has_animation=_has_animation(image_facts, video_stream),
        video_codec=_optional_str(video_stream.get("codec_name")),
        pixel_format=_optional_str(video_stream.get("pix_fmt")),
        has_audio=audio_stream is not None,
        audio_codec=(
            _optional_str(audio_stream.get("codec_name"))
            if audio_stream is not None
            else None
        ),
    )


def try_inspect_image(path: Path) -> ImageFacts | None:
    """Return Pillow facts when this is a supported image; otherwise None.

    An MP4 is not an error here—it simply is not a Pillow image. A damaged GIF
    or WebP should raise from `inspect_image`, rather than being hidden.
    """
    try:
        return inspect_image(path)
    except UnidentifiedImageError:
        return None


def _first_stream_of_type(
    probe: dict[str, Any], stream_type: str
) -> dict[str, Any] | None:
    """Return the first ffprobe stream whose codec type matches."""
    return next(
        (
            stream
            for stream in probe.get("streams", [])
            if stream.get("codec_type") == stream_type
        ),
        None,
    )


def _mime_type(source: Path, image_facts: ImageFacts | None) -> str | None:
    """Prefer Pillow's detected image MIME type, else use the file extension."""
    if image_facts is not None and image_facts.mime_type is not None:
        return image_facts.mime_type

    return mimetypes.guess_type(source.name)[0]


def _preferred_int(preferred: object, fallback: object) -> int | None:
    """Use a reliable preferred value, falling back to an ffprobe value."""
    return (
        _optional_int(preferred) if preferred is not None else _optional_int(fallback)
    )


def _optional_int(value: object) -> int | None:
    """Safely parse nullable ffprobe numeric fields."""
    if value in (None, "", "N/A"):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    """Return a non-blank string, otherwise None."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _frame_rate(video_stream: dict[str, Any]) -> float | None:
    """Parse ffprobe's average rate, then its nominal stream rate."""
    return _fraction_to_float(video_stream.get("avg_frame_rate")) or _fraction_to_float(
        video_stream.get("r_frame_rate")
    )


def _fraction_to_float(value: object) -> float | None:
    """Convert ffprobe values such as '30000/1001' to a float."""
    if value in (None, "", "N/A", "0/0"):
        return None

    try:
        numerator_text, denominator_text = str(value).split("/", maxsplit=1)
        numerator = float(numerator_text)
        denominator = float(denominator_text)

        if denominator == 0:
            return None

        return numerator / denominator
    except (TypeError, ValueError):
        return None


def _duration_ms(
    probe: dict[str, Any],
    video_stream: dict[str, Any],
    image_facts: ImageFacts | None,
) -> int | None:
    """Prefer container duration, then stream duration, then Pillow timing."""
    format_duration = _seconds_to_ms(probe.get("format", {}).get("duration"))
    if format_duration is not None:
        return format_duration

    stream_duration = _seconds_to_ms(video_stream.get("duration"))
    if stream_duration is not None:
        return stream_duration

    return image_facts.duration_ms if image_facts is not None else None


def _seconds_to_ms(value: object) -> int | None:
    """Convert ffprobe duration strings in seconds to milliseconds."""
    if value in (None, "", "N/A"):
        return None

    try:
        return round(float(value) * 1_000)
    except (TypeError, ValueError):
        return None


def _has_animation(
    image_facts: ImageFacts | None,
    video_stream: dict[str, Any],
) -> bool | None:
    """Determine whether the file represents moving visual media."""
    if image_facts is not None:
        return image_facts.has_animation

    # An ffprobe video stream represents video media even when its exact frame
    # count is unavailable.
    return video_stream.get("codec_type") == "video"
