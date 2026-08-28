"""Emote lookup and creation services."""

from __future__ import annotations

from sqlmodel import Session, select

from gif_finder.database.models import Emote, Media


class EmoteService:
    """Encapsulate emote creation, lookup and listing operations."""

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Emote]:
        """Return every emote ordered by id."""
        statement = select(Emote).order_by(Emote.id)
        return list(self.session.exec(statement).all())

    def get_by_id(self, emote_id: int) -> Emote | None:
        """Fetch an emote by id."""
        return self.session.get(Emote, emote_id)

    def get_by_name(self, name: str) -> Emote | None:
        """Fetch an emote by exact name."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Emote name cannot be blank.")
        return self.session.exec(
            select(Emote).where(Emote.name == cleaned_name)
        ).first()

    def create(self, *, name: str, media_id: int | None = None) -> Emote:
        """Create an emote and optionally assign it to a media row."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Emote name cannot be blank.")

        emote = Emote(name=cleaned_name)
        self.session.add(emote)
        self.session.flush()

        if media_id is not None:
            media = self.session.get(Media, media_id)
            if media is None:
                raise ValueError(f"Media row {media_id} does not exist.")
            media.emote_id = emote.id

        self.session.commit()
        self.session.refresh(emote)
        return emote

    def find_or_create(self, *, name: str, media_id: int | None = None) -> Emote:
        """Return an existing emote or create one."""
        existing = self.get_by_name(name)
        if existing is not None:
            if media_id is not None:
                media = self.session.get(Media, media_id)
                if media is not None:
                    media.emote_id = existing.id
                    self.session.commit()
            return existing
        return self.create(name=name, media_id=media_id)
