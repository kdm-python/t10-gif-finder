from pathlib import Path

from PIL import Image

from gif_finder.database.models import Media
from gif_finder.services.media import prepare_media
from gif_finder.services.storage import store_media


def test_store_media_copies_file_to_media_root(tmp_path: Path):
    source = tmp_path / "source" / "sample.gif"
    source.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (10, 10), color="red")
    image.save(source, format="GIF")

    destination_root = tmp_path / "media"
    stored = store_media(source, destination_root=destination_root)

    assert stored.file_hash
    assert Path(stored.file_path).exists()
    assert Path(stored.file_path).parent.parent == destination_root
    assert Path(stored.file_path).suffix == ".gif"


def test_prepare_media_builds_database_row(tmp_path: Path):
    source = tmp_path / "to_insert" / "example.gif"
    source.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (20, 20), color="blue")
    image.save(source, format="GIF")

    destination_root = tmp_path / "media"
    row = prepare_media(
        source,
        author="tester",
        stream_id=7,
        destination_root=destination_root,
    )

    assert isinstance(row, Media)
    assert row.original_filename == "example.gif"
    assert row.author == "tester"
    assert row.stream_id == 7
    assert row.format == "GIF"
    assert row.mime_type == "image/gif"
    assert row.file_size > 0
    assert Path(row.file_path).exists()
