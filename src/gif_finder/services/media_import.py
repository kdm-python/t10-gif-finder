"""Import media data into the database."""

from pathlib import Path

from sqlmodel import Session

from gif_finder.database.database import get_session
from gif_finder.database.models import Media
from gif_finder.services.media import prepare_media


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
    # ...

    # 4. Create MediaTag relationships
    # ...

    # 5. Commit everything
    session.commit()

    # 6. Refresh to get generated ID
    session.refresh(media)

    return media
