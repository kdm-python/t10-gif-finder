"""Emote CRUD endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from gif_finder.api.dependencies import get_db_session
from gif_finder.api.schemas import EmoteCreate, EmoteRead
from gif_finder.logger import logger
from gif_finder.services.emote import EmoteService

router = APIRouter(prefix="/emotes", tags=["emotes"])
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=list[EmoteRead])
def list_emotes(session: SessionDep) -> list[EmoteRead]:
    return [EmoteRead.model_validate(emote) for emote in EmoteService(session).list()]


@router.get("/{emote_id}", response_model=EmoteRead)
def get_emote(emote_id: int, session: SessionDep) -> EmoteRead:
    emote = EmoteService(session).get_by_id(emote_id)
    if emote is None:
        raise HTTPException(status_code=404, detail="Emote not found.")
    return EmoteRead.model_validate(emote)


@router.post("", response_model=EmoteRead, status_code=status.HTTP_201_CREATED)
def create_emote(payload: EmoteCreate, session: SessionDep) -> EmoteRead:
    service = EmoteService(session)
    if service.get_by_name(payload.name) is not None:
        raise HTTPException(status_code=409, detail="An emote with this name already exists.")
    emote = service.create(name=payload.name, media_id=payload.media_id)
    logger.info("Created emote {}", emote.id)
    return EmoteRead.model_validate(emote)


@router.delete("/{emote_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emote(emote_id: int, session: SessionDep) -> Response:
    service = EmoteService(session)
    if service.get_by_id(emote_id) is None:
        raise HTTPException(status_code=404, detail="Emote not found.")
    try:
        service.delete(emote_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    logger.info("Deleted emote {}", emote_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
