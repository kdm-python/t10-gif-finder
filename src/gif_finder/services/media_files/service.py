
from dataclasses import dataclass
from pathlib import Path

from gif_finder.services.media_files.inspector import MediaFileInfo
from gif_finder.services.media_files.repository import Media
from gif_finder.services.media_files.storage import StoredMedia


@dataclass(frozen=True)
class MediaImportRequest:
    source_path: Path
    tags: list[str]
    author: str | None = None
    stream_id: int | None = None


class MediaFilesService:
    def inspect(self, source: Path) -> MediaFileInfo: ...
    def import_media(self, request: MediaImportRequest) -> Media: ...
    def list_media(...): ...
    def delete_media(self, media_id: int) -> None: ...
