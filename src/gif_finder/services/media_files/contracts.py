from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class MediaFileInfo:
    """Normalised technical metadata produced by media inspection."""

    source_path: Path
    file_size_bytes: int
    media_kind: Literal["image", "video"]

    container_format: str | None = None
    mime_type: str | None = None

    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    frame_count: int | None = None
    frame_rate: float | None = None
    has_animation: bool | None = None
    has_alpha: bool | None = None
    rotation_degrees: int | None = None

    video_codec: str | None = None
    pixel_format: str | None = None
    video_bitrate: int | None = None

    has_audio: bool = False
    audio_codec: str | None = None
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    audio_bitrate: int | None = None

    # Raw JSON from ffprobe; JSON-serialisable by construction.
    probe_data: dict[str, Any] = field(default_factory=dict)
    probe_version: str | None = None


@dataclass(frozen=True)
class MediaImportRequest:
    """Request to import a media file, including metadata and tags."""

    source_path: Path
    tags: list[str]
    original_filename: str | None = None

    author: str | None = None
    emote_name: str | None = None
    stream_id: int | None = None
    title: str | None = None
    description: str | None = None
    source_url: str | None = None


@dataclass(frozen=True)
class MediaUpdateRequest:
    """A partial update of user-maintained media catalogue fields."""

    provided_fields: frozenset[str]
    title: str | None = None
    description: str | None = None
    author: str | None = None
    source_url: str | None = None
    stream_id: int | None = None
    emote_id: int | None = None
    tags: list[str] | None = None


@dataclass(frozen=True)
class StoredMedia:
    """Reference to one object in the content-addressed media store."""

    content_hash: str
    storage_key: str
    original_filename: str
    file_size_bytes: int
    was_created: bool
