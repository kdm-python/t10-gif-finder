"""Twitch clip catalogue endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from gif_finder.api.dependencies import get_db_session
from gif_finder.api.schemas import TwitchClipCreate, TwitchClipRead, twitch_clip_read
from gif_finder.logger import logger
from gif_finder.services.twitch.api import (
    InvalidTwitchClipUrl,
    TwitchClientError,
    TwitchClipNotFound,
    TwitchConfigurationError,
)
from gif_finder.services.twitch.service import TwitchService

router = APIRouter(prefix="/twitch/clips", tags=["twitch"])
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=list[TwitchClipRead])
def list_twitch_clips(session: SessionDep) -> list[TwitchClipRead]:
    return [twitch_clip_read(clip) for clip in TwitchService.from_settings(session).list()]


@router.get("/{clip_id}", response_model=TwitchClipRead)
def get_twitch_clip(clip_id: int, session: SessionDep) -> TwitchClipRead:
    clip = TwitchService.from_settings(session).get_by_id(clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Twitch clip not found.")
    return twitch_clip_read(clip)


@router.post("", response_model=TwitchClipRead, status_code=status.HTTP_201_CREATED)
def import_twitch_clip(
    payload: TwitchClipCreate, response: Response, session: SessionDep
) -> TwitchClipRead:
    try:
        clip, created = TwitchService.from_settings(session).import_url(payload.url)
    except InvalidTwitchClipUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TwitchClipNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TwitchConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TwitchClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not created:
        response.status_code = status.HTTP_200_OK
    logger.info("{} Twitch clip {}", "Imported" if created else "Found", clip.id)
    return twitch_clip_read(clip)


@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_twitch_clip(clip_id: int, session: SessionDep) -> Response:
    if not TwitchService.from_settings(session).delete(clip_id):
        raise HTTPException(status_code=404, detail="Twitch clip not found.")
    logger.info("Deleted Twitch clip {}", clip_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
