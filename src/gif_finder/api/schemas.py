"""Pydantic request and response models for the HTTP API."""

from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from gif_finder.database.models import Media


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class EmoteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    media_id: int | None = None


class EmoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class StreamCreate(BaseModel):
    stream_date: date
    description: str | None = None


class StreamUpdate(BaseModel):
    stream_date: date | None = None
    description: str | None = None


class StreamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stream_date: date
    description: str | None


class MediaUpdate(BaseModel):
    """Only catalogue fields can be edited after import."""

    title: str | None = Field(default=None, max_length=512)
    description: str | None = None
    author: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=2048)
    stream_id: int | None = None
    emote_id: int | None = None
    tags: list[str] | None = None


class MediaRead(BaseModel):
    """Safe catalogue representation; raw probe JSON and paths stay internal."""

    id: int
    content_hash: str
    original_filename: str
    original_extension: str | None
    file_size_bytes: int
    media_kind: str
    format: str
    mime_type: str
    width: int
    height: int
    duration_ms: int | None
    frame_count: int | None
    frame_rate: float | None
    has_animation: bool
    has_alpha: bool | None
    rotation_degrees: int | None
    video_codec: str | None
    pixel_format: str | None
    video_bitrate: int | None
    has_audio: bool
    audio_codec: str | None
    audio_channels: int | None
    audio_sample_rate: int | None
    audio_bitrate: int | None
    title: str | None
    description: str | None
    author: str | None
    source_url: str | None
    emote_id: int | None
    stream_id: int | None
    probe_version: str | None
    imported_at: datetime
    updated_at: datetime
    tags: list[str]
    file_url: str


class ErrorResponse(BaseModel):
    detail: str


def media_read(media: Media, tags: list[str]) -> MediaRead:
    """Build a browser-safe API response from a stored media model."""
    if media.id is None:  # pragma: no cover - persisted API rows always have IDs
        raise ValueError("Cannot serialise media without an ID.")

    return MediaRead(
        id=media.id,
        content_hash=media.content_hash,
        original_filename=media.original_filename,
        original_extension=media.original_extension,
        file_size_bytes=media.file_size_bytes,
        media_kind=media.media_kind,
        format=media.format,
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        duration_ms=media.duration_ms,
        frame_count=media.frame_count,
        frame_rate=media.frame_rate,
        has_animation=media.has_animation,
        has_alpha=media.has_alpha,
        rotation_degrees=media.rotation_degrees,
        video_codec=media.video_codec,
        pixel_format=media.pixel_format,
        video_bitrate=media.video_bitrate,
        has_audio=media.has_audio,
        audio_codec=media.audio_codec,
        audio_channels=media.audio_channels,
        audio_sample_rate=media.audio_sample_rate,
        audio_bitrate=media.audio_bitrate,
        title=media.title,
        description=media.description,
        author=media.author,
        source_url=media.source_url,
        emote_id=media.emote_id,
        stream_id=media.stream_id,
        probe_version=media.probe_version,
        imported_at=media.imported_at,
        updated_at=media.updated_at,
        tags=tags,
        file_url=f"/media/{media.id}/file",
    )
