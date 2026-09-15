from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredMedia:
    content_hash: str
    storage_key: str
    original_filename: str
    file_size_bytes: int


class MediaStorage:
    def store(self, source: Path) -> StoredMedia: ...
    def resolve(self, storage_key: str) -> Path: ...
    def delete_if_unreferenced(self, storage_key: str) -> None: ...
