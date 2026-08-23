"""Import media data into the database."""

from pathlib import Path

from sqlmodel import Session, select

from gif_finder.database.database import get_session
from gif_finder.database.models import Media, MediaTag, Tag
from gif_finder.services.media import prepare_media


def find_or_create_tag(session: Session, tag_name: str) -> Tag:
    """Find a Tag by name, or create it if it doesn't exist."""
    tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
    if tag is None:
        tag = Tag(name=tag_name)
        session.add(tag)
        session.commit()
        session.refresh(tag)
    return tag


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
    tag_objects = [find_or_create_tag(session, tag_name) for tag_name in tags]

    # 4. Create MediaTag relationships
    for tag in tag_objects:
        media_tag = MediaTag(media_id=media.id, tag_id=tag.id)
        session.add(media_tag)

    # 5. Commit everything
    session.commit()

    # 6. Refresh to get generated ID
    session.refresh(media)

    return media


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: uv run src/gif_finder/services/media_import.py <path> <tag1,tag2,...>"
        )
        raise SystemExit(1)

    path = Path(sys.argv[1])
    tags = sys.argv[2].split(",")

    with get_session() as session:
        media = import_media(session, path, tags=tags, frame_rate=24)

    print(media)
