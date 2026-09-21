from pathlib import Path

from gif_finder.services.media_files.ffprobe import run_ffprobe
from gif_finder.services.media_files.images import inspect_image

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_ffprobe_reads_a_gif_fixture():
    payload = run_ffprobe(FIXTURES / "gif" / "animated_floor.gif")

    assert payload["format"]["format_name"] == "gif"
    assert payload["streams"][0]["codec_type"] == "video"
    assert payload["streams"][0]["width"] == 640
    assert payload["streams"][0]["height"] == 360


def test_pillow_reads_animated_webp_dimensions_and_frames():
    facts = inspect_image(FIXTURES / "webp" / "head_in_hands.webp")

    assert facts.format == "WEBP"
    assert (facts.width, facts.height) == (640, 433)
    assert facts.frame_count == 89
    assert facts.has_animation is True
