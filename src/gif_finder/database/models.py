from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel import Field, SQLModel


@dataclass
class MediaMetadata:
    format: str
    mime_type: str
    width: int
    height: int
    file_size: int
    frame_count: int
    frame_rate: float | None
    duration_ms: int | None
    has_animation: bool


# --- Database Models ---


class Stream(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    stream_date: date
    description: str


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class MediaTag(SQLModel, table=True):
    media_id: int = Field(foreign_key="media.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)


class Emote(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    media_id: int = Field(foreign_key="media.id")


class Media(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    file_path: str
    original_filename: str

    format: str
    mime_type: str

    file_size: int
    width: int
    height: int

    frame_count: int
    frame_rate: float | None = None
    duration_ms: int | None = None
    has_animation: bool = False

    author: str | None = None

    stream_id: int | None = Field(
        default=None,
        foreign_key="stream.id",
    )

    # description: str | None = None

    file_hash: str | None = None

    imported_at: datetime = Field(default_factory=datetime.now)
