"""Application workflows for cataloguing Twitch clips."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from gif_finder.database.models import TwitchClip
from gif_finder.services.twitch.api import TwitchClient, get_clip_id


class TwitchService:
    """Coordinate Twitch metadata lookup and local catalogue persistence."""

    def __init__(self, session: Session, client: TwitchClient) -> None:
        self.session = session
        self.client = client

    @classmethod
    def from_settings(cls, session: Session) -> "TwitchService":
        return cls(session, TwitchClient.from_settings())

    def list(self) -> list[TwitchClip]:
        return list(self.session.exec(select(TwitchClip).order_by(TwitchClip.id)).all())

    def get_by_id(self, clip_id: int) -> TwitchClip | None:
        return self.session.get(TwitchClip, clip_id)

    def get_by_twitch_id(self, twitch_clip_id: str) -> TwitchClip | None:
        return self.session.exec(
            select(TwitchClip).where(TwitchClip.twitch_clip_id == twitch_clip_id)
        ).first()

    def import_url(self, url: str) -> tuple[TwitchClip, bool]:
        twitch_clip_id = get_clip_id(url)
        existing = self.get_by_twitch_id(twitch_clip_id)
        if existing is not None:
            return existing, False

        data = self.client.get_clip(twitch_clip_id)
        clip = TwitchClip(**data.__dict__)
        self.session.add(clip)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.get_by_twitch_id(twitch_clip_id)
            if existing is not None:
                return existing, False
            raise
        self.session.refresh(clip)
        return clip, True

    def delete(self, clip_id: int) -> bool:
        clip = self.get_by_id(clip_id)
        if clip is None:
            return False
        self.session.delete(clip)
        self.session.commit()
        return True
