"""Tag persistence and lookup services."""

from __future__ import annotations

from sqlmodel import Session, select

from gif_finder.database.models import MediaTag, Tag


class TagService:
    """Encapsulate tag creation, lookup and listing operations."""

    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Tag]:
        """Return every tag ordered by id."""
        statement = select(Tag).order_by(Tag.id)
        return list(self.session.exec(statement).all())

    def get_by_id(self, tag_id: int) -> Tag | None:
        """Fetch a tag by primary key."""
        return self.session.get(Tag, tag_id)

    def get_by_name(self, name: str) -> Tag | None:
        """Fetch a tag by a case-sensitive exact name value."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Tag name cannot be blank.")
        return self.session.exec(select(Tag).where(Tag.name == cleaned_name)).first()

    def create(self, name: str) -> Tag:
        """Create a new tag row."""
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Tag name cannot be blank.")

        tag = Tag(name=cleaned_name)
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag

    def find_or_create(self, name: str) -> Tag:
        """Return an existing tag or create one if it is missing."""
        existing = self.get_by_name(name)
        if existing is not None:
            return existing
        return self.create(name)

    def delete(self, tag_id: int) -> None:
        """Delete a tag, raising if it is still attached to media."""
        tag = self.session.get(Tag, tag_id)
        if tag is None:
            raise ValueError(f"Tag {tag_id} does not exist.")

        in_use = self.session.exec(
            select(MediaTag).where(MediaTag.tag_id == tag_id)
        ).first()
        if in_use is not None:
            raise ValueError(
                f"Tag {tag_id} is still attached to media and cannot be deleted."
            )

        self.session.delete(tag)
        self.session.commit()
