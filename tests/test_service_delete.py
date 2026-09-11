"""Unit tests for delete/list additions on the Tag/Stream/Emote/Media services."""

from datetime import date
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from gif_finder.database.models import Media, MediaTag
from gif_finder.services.emote import EmoteService
from gif_finder.services.media.media_service import MediaService
from gif_finder.services.stream import StreamService
from gif_finder.services.tag import TagService


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _make_media(session: Session, tmp_path: Path, **overrides) -> Media:
    file_path = tmp_path / "media.gif"
    file_path.write_bytes(b"fake-gif-bytes")

    media = Media(
        file_path=str(file_path),
        original_filename="media.gif",
        format="GIF",
        mime_type="image/gif",
        file_size=file_path.stat().st_size,
        width=10,
        height=10,
        frame_count=1,
        **overrides,
    )
    session.add(media)
    session.commit()
    session.refresh(media)
    return media


def test_tag_delete_removes_unused_tag(session):
    tag = TagService(session).create("foo")
    TagService(session).delete(tag.id)
    assert TagService(session).get_by_id(tag.id) is None


def test_tag_delete_raises_when_in_use(session, tmp_path):
    tag = TagService(session).create("foo")
    media = _make_media(session, tmp_path)
    session.add(MediaTag(media_id=media.id, tag_id=tag.id))
    session.commit()

    with pytest.raises(ValueError):
        TagService(session).delete(tag.id)


def test_stream_delete_raises_when_in_use(session, tmp_path):
    stream = StreamService(session).create(stream_date=date(2024, 1, 1), description="")
    _make_media(session, tmp_path, stream_id=stream.id)

    with pytest.raises(ValueError):
        StreamService(session).delete(stream.id)


def test_emote_delete_raises_when_in_use(session, tmp_path):
    emote = EmoteService(session).create(name="pog")
    _make_media(session, tmp_path, emote_id=emote.id)

    with pytest.raises(ValueError):
        EmoteService(session).delete(emote.id)


def test_media_service_list_filters_by_author(session, tmp_path):
    _make_media(session, tmp_path, author="alice")
    _make_media(session, tmp_path, author="bob")

    rows = MediaService(session).list(author="alice")

    assert len(rows) == 1
    assert rows[0].author == "alice"


def test_media_service_delete_removes_row_and_file(session, tmp_path):
    media = _make_media(session, tmp_path)
    file_path = Path(media.file_path)
    assert file_path.exists()

    MediaService(session).delete(media.id)

    assert MediaService(session).get_by_id(media.id) is None
    assert not file_path.exists()
