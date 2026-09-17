from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel, UniqueConstraint


class Stream(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    stream_date: date
    description: str | None = None


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class MediaTag(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("media_id", "tag_id", name="uq_media_tag"),)

    media_id: int = Field(foreign_key="media.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Emote(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class Media(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Storage identity: no machine-specific absolute paths.
    content_hash: str = Field(unique=True, index=True, max_length=64)
    storage_key: str = Field(unique=True, max_length=255)
    original_filename: str = Field(max_length=512)
    original_extension: str | None = Field(default=None, max_length=32)
    file_size_bytes: int

    # Broad category and container/image type.
    media_kind: str = Field(index=True, max_length=16)  # "image" or "video"
    format: str = Field(index=True, max_length=32)  # GIF, WEBP, MP4
    mime_type: str = Field(index=True, max_length=128)

    # Visual properties.
    width: int
    height: int
    duration_ms: int | None = Field(default=None, index=True)
    frame_count: int | None = None
    frame_rate: float | None = None
    has_animation: bool = False
    has_alpha: bool | None = None
    rotation_degrees: int | None = None

    # Video/audio details; null for formats where they do not apply.
    video_codec: str | None = Field(default=None, index=True, max_length=64)
    pixel_format: str | None = Field(default=None, max_length=64)
    video_bitrate: int | None = None

    has_audio: bool = False
    audio_codec: str | None = Field(default=None, index=True, max_length=64)
    audio_channels: int | None = None
    audio_sample_rate: int | None = None
    audio_bitrate: int | None = None

    # User-maintained catalogue data.
    title: str | None = Field(default=None, index=True, max_length=512)
    description: str | None = None
    author: str | None = Field(default=None, index=True, max_length=255)
    source_url: str | None = Field(default=None, max_length=2048)

    emote_id: int | None = Field(default=None, foreign_key="emote.id", index=True)
    stream_id: int | None = Field(default=None, foreign_key="stream.id", index=True)

    # Optional diagnostic preservation of ffprobe's format/stream JSON.
    probe_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    probe_version: str | None = Field(default=None, max_length=64)

    imported_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
