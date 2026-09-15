"""Integration tests for the isolated media-files inspection service."""

from __future__ import annotations

from pathlib import Path

import pytest

from gif_finder.services.media_files.inspector import (
    MediaInspectionError,
    inspect_media_file,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_inspect_static_gif() -> None:
    """A static GIF still has valid visual metadata but is not animated."""
    info = inspect_media_file(FIXTURES / "small_floor.gif")

    assert info.source_path == (FIXTURES / "small_floor.gif").resolve()
    assert info.file_size_bytes == 68

    assert info.container_format == "gif"
    assert info.mime_type == "image/gif"
    assert info.video_codec == "gif"

    assert info.width == 16
    assert info.height == 16
    assert info.frame_count == 1
    assert info.has_animation is False
    assert info.has_audio is False
    assert info.audio_codec is None


def test_inspect_animated_gif() -> None:
    info = inspect_media_file(FIXTURES / "animated_floor.gif")

    assert info.container_format == "gif"
    assert info.mime_type == "image/gif"
    assert info.video_codec == "gif"
    assert info.pixel_format == "bgra"

    assert (info.width, info.height) == (640, 360)
    assert info.frame_count == 72
    assert info.duration_ms == 2_850
    assert info.has_animation is True
    assert info.has_audio is False


@pytest.mark.parametrize(
    ("filename", "expected_size", "expected_frames"),
    [
        ("head_in_hands.webp", (640, 433), 89),
        ("ray_gift_muzz.webp", (640, 769), 80),
    ],
)
def test_inspect_animated_webp_uses_pillow_facts(
    filename: str,
    expected_size: tuple[int, int],
    expected_frames: int,
) -> None:
    """Pillow supplies image facts when ffprobe cannot obtain WebP dimensions."""
    info = inspect_media_file(FIXTURES / filename)

    assert info.video_codec == "webp"
    assert info.mime_type == "image/webp"

    assert (info.width, info.height) == expected_size
    assert info.frame_count == expected_frames
    assert info.has_animation is True
    assert info.has_audio is False


def test_inspect_missing_file_raises_clear_error() -> None:
    """A nonexistent source must fail before ffprobe is called."""
    missing_file = FIXTURES / "does_not_exist.gif"

    with pytest.raises(FileNotFoundError, match="Media file does not exist"):
        inspect_media_file(missing_file)


def test_inspect_directory_raises_clear_error() -> None:
    """A directory must not be handed to ffprobe as a media file."""
    with pytest.raises(MediaInspectionError, match="Media path is not a file"):
        inspect_media_file(FIXTURES)
