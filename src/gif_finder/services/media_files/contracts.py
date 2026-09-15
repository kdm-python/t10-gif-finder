from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaFileInfo:
    source_path: Path
    file_size_bytes: int

    container_format: str | None
    mime_type: str | None

    width: int | None
    height: int | None
    frame_count: int | None
    frame_rate: float | None
    duration_ms: int | None
    has_animation: bool | None

    video_codec: str | None = None
    pixel_format: str | None = None
    has_audio: bool = False
    audio_codec: str | None = None
