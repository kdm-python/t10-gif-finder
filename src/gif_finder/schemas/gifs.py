"""Schemas for GIF-related data."""

from pydantic import BaseModel


# Only thing required is one or more tags, everything else is optional
class MediaCreate(BaseModel):
    tags: list[str]
    author: str | None = None
    stream_id: int | None = None
    emotes: list[str] = []


class MediaRead(BaseModel):
    id: int
    file_path: str
    original_filename: str
    format: str
    mime_type: str
    width: int
    height: int
    file_size: int
    frame_count: int
    frame_rate: float | None = None
    duration_ms: int | None = None
    has_animation: bool = False


class MediaUpdate(BaseModel):
    tags: list[str] | None = None
    author: str | None = None
    stream_id: int | None = None
    emotes: list[str] | None = None
