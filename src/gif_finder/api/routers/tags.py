"""Tag CRUD endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from gif_finder.api.dependencies import get_db_session
from gif_finder.api.schemas import TagCreate, TagRead
from gif_finder.logger import logger
from gif_finder.services.tag import TagService

router = APIRouter(prefix="/tags", tags=["tags"])
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=list[TagRead])
def list_tags(session: SessionDep) -> list[TagRead]:
    return [TagRead.model_validate(tag) for tag in TagService(session).list()]


@router.get("/{tag_id}", response_model=TagRead)
def get_tag(tag_id: int, session: SessionDep) -> TagRead:
    tag = TagService(session).get_by_id(tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found.")
    return TagRead.model_validate(tag)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, session: SessionDep) -> TagRead:
    service = TagService(session)
    if service.get_by_name(payload.name) is not None:
        raise HTTPException(status_code=409, detail="A tag with this name already exists.")
    tag = service.create(payload.name)
    logger.info("Created tag {}", tag.id)
    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, session: SessionDep) -> Response:
    service = TagService(session)
    if service.get_by_id(tag_id) is None:
        raise HTTPException(status_code=404, detail="Tag not found.")
    try:
        service.delete(tag_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    logger.info("Deleted tag {}", tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
