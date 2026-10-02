"""Normalised values exchanged by the Twitch API client and service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TwitchClipData:
    twitch_clip_id: str
    broadcaster_id: str
    broadcaster_name: str
    creator_id: str | None
    creator_name: str | None
    video_id: str | None
    game_id: str | None
    vod_offset: int | None
    title: str
    language: str | None
    duration: float
    created_at: datetime
