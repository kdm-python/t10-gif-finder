from __future__ import annotations

from pathlib import Path

from gif_finder.services.media_files.contracts import MediaImportRequest
from gif_finder.services.media_files.service import MediaFilesService
from gif_finder.services.media_files.storage import MediaStorage


FIXTURE = Path(__file__).parent.parent / "fixtures" / "gif" / "animated_floor.gif"


def test_import_merges_duplicate_content_and_tags(db_session, tmp_path: Path) -> None:
    storage = MediaStorage(tmp_path / "media")
    service = MediaFilesService(db_session, storage)

    first = service.import_media(
        MediaImportRequest(
            source_path=FIXTURE,
            tags=["Funny"],
            author="tester",
            emote_name="party",
            title="Animated floor",
        )
    )
    second = service.import_media(
        MediaImportRequest(
            source_path=FIXTURE,
            tags=["reaction", "funny"],
        )
    )

    assert first.id == second.id
    assert second.content_hash
    assert storage.resolve(second.storage_key).exists()
    assert second.probe_data["format"]["format_name"] == "gif"
    assert service.get_tags_for_media([second.id]) == {second.id: ["funny", "reaction"]}


def test_delete_removes_catalogue_row_and_stored_file(db_session, tmp_path: Path) -> None:
    storage = MediaStorage(tmp_path / "media")
    service = MediaFilesService(db_session, storage)
    media = service.import_media(
        MediaImportRequest(source_path=FIXTURE, tags=["funny"])
    )
    stored_path = storage.resolve(media.storage_key)

    service.delete_media(media.id)

    assert service.repository.get_by_id(media.id) is None
    assert not stored_path.exists()
