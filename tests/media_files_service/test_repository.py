from pathlib import Path

from gif_finder.services.media_files.contracts import (
    MediaFileInfo,
    MediaImportRequest,
    StoredMedia,
)
from gif_finder.services.media_files.repository import MediaRepository


def test_create_media_maps_full_inspection_result(db_session):
    repository = MediaRepository(db_session)

    info = MediaFileInfo(
        source_path=Path("/input/example.gif"),
        file_size_bytes=1234,
        media_kind="image",
        container_format="gif",
        mime_type="image/gif",
        width=640,
        height=360,
        duration_ms=2850,
        frame_count=72,
        frame_rate=25.0,
        has_animation=True,
        video_codec="gif",
        pixel_format="bgra",
        probe_data={
            "format": {"format_name": "gif"},
            "streams": [{"codec_name": "gif"}],
        },
    )
    stored = StoredMedia(
        content_hash="a" * 64,
        storage_key=f"aa/{'a' * 64}",
        original_filename="example.gif",
        file_size_bytes=1234,
        was_created=True,
    )
    request = MediaImportRequest(
        source_path=info.source_path,
        tags=["funny"],
        author="Kyle",
    )

    media = repository.create_media(
        info=info,
        stored=stored,
        request=request,
        emote_id=None,
    )
    repository.attach_tags(media, request.tags)

    db_session.commit()
    db_session.refresh(media)

    assert media.content_hash == stored.content_hash
    assert media.storage_key == stored.storage_key
    assert media.duration_ms == 2850
    assert media.probe_data["format"]["format_name"] == "gif"


def test_repository_normalises_tags_and_creates_one_emote(db_session):
    repository = MediaRepository(db_session)
    first_tag = repository.find_or_create_tag(" Funny ")
    second_tag = repository.find_or_create_tag("funny")
    emote = repository.find_or_create_emote("party")

    db_session.commit()

    assert first_tag.id == second_tag.id
    assert first_tag.name == "funny"
    assert emote.name == "party"
