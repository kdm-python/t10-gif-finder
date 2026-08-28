"""Import media data into the database."""

from pathlib import Path

from sqlmodel import Session

from gif_finder.database.models import Media, MediaTag, Tag
from gif_finder.services.media import prepare_media
from gif_finder.services.tag import TagService


def find_or_create_tag(session: Session, tag_name: str) -> Tag:
    """Backward-compatible helper for tag lookup or creation."""
    return TagService(session).find_or_create(tag_name)


def import_media(
    session: Session,
    media_file: Path,
    *,
    tags: list[str],
    author: str | None = None,
    stream_id: int | None = None,
    frame_rate: float | None = None,
) -> Media:
    # 1. Prepare physical file + Media object
    media = prepare_media(
        media_file,
        author=author,
        stream_id=stream_id,
        frame_rate=frame_rate,
    )

    # 2. Add Media to session
    session.add(media)

    # 3. Create/find tags
    tag_objects = [TagService(session).find_or_create(tag_name) for tag_name in tags]

    # 4. Create MediaTag relationships
    for tag in tag_objects:
        media_tag = MediaTag(media_id=media.id, tag_id=tag.id)
        session.add(media_tag)

    # 5. Commit everything
    session.commit()

    # 6. Refresh to get generated ID
    session.refresh(media)

    return media
