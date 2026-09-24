"""Stream CRUD endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from gif_finder.api.dependencies import get_db_session
from gif_finder.api.schemas import StreamCreate, StreamRead, StreamUpdate
from gif_finder.logger import logger
from gif_finder.services.stream import StreamService

router = APIRouter(prefix="/streams", tags=["streams"])
SessionDep = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=list[StreamRead])
def list_streams(session: SessionDep) -> list[StreamRead]:
    return [StreamRead.model_validate(stream) for stream in StreamService(session).list()]


@router.get("/{stream_id}", response_model=StreamRead)
def get_stream(stream_id: int, session: SessionDep) -> StreamRead:
    stream = StreamService(session).get_by_id(stream_id)
    if stream is None:
        raise HTTPException(status_code=404, detail="Stream not found.")
    return StreamRead.model_validate(stream)


@router.post("", response_model=StreamRead, status_code=status.HTTP_201_CREATED)
def create_stream(payload: StreamCreate, session: SessionDep) -> StreamRead:
    stream = StreamService(session).create(
        stream_date=payload.stream_date,
        description=payload.description or "",
    )
    logger.info("Created stream {}", stream.id)
    return StreamRead.model_validate(stream)


@router.patch("/{stream_id}", response_model=StreamRead)
def update_stream(
    stream_id: int, payload: StreamUpdate, session: SessionDep
) -> StreamRead:
    fields = set(payload.model_fields_set)
    if not fields:
        raise HTTPException(status_code=422, detail="Provide at least one field to update.")
    try:
        stream = StreamService(session).update(
            stream_id,
            provided_fields=fields,
            **payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        if "does not exist" in str(exc):
            raise HTTPException(status_code=404, detail="Stream not found.") from exc
        raise
    logger.info("Updated stream {} fields={}", stream_id, sorted(fields))
    return StreamRead.model_validate(stream)


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stream(stream_id: int, session: SessionDep) -> Response:
    service = StreamService(session)
    if service.get_by_id(stream_id) is None:
        raise HTTPException(status_code=404, detail="Stream not found.")
    try:
        service.delete(stream_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    logger.info("Deleted stream {}", stream_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
