"""Media import, catalogue, delivery, and deletion endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlmodel import Session

from gif_finder.api.dependencies import get_db_session
from gif_finder.api.schemas import MediaRead, MediaUpdate, media_read
from gif_finder.api.uploads import TemporaryUpload, cleanup_upload, save_upload
from gif_finder.config import settings
from gif_finder.logger import logger
from gif_finder.services.media_files.contracts import (
    MediaImportRequest,
    MediaUpdateRequest,
)
from gif_finder.services.media_files.service import (
    MediaFilesService,
    MediaFilesServiceError,
)
from gif_finder.services.media_files.storage import MediaStorageError

router = APIRouter(prefix="/media", tags=["media"])
SessionDep = Annotated[Session, Depends(get_db_session)]


def _read_media(service: MediaFilesService, media_id: int) -> MediaRead:
    media = service.get_media(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found.")
    tags = service.get_tags_for_media([media_id]).get(media_id, [])
    return media_read(media, tags)


@router.get("", response_model=list[MediaRead])
def list_media(session: SessionDep) -> list[MediaRead]:
    service = MediaFilesService.from_settings(session)
    records = service.list_media()
    tags_by_media = service.get_tags_for_media(
        [media.id for media in records if media.id is not None]
    )
    return [media_read(media, tags_by_media.get(media.id, [])) for media in records]


@router.get("/{media_id}/file", response_class=FileResponse)
def get_media_file(media_id: int, session: SessionDep) -> FileResponse:
    service = MediaFilesService.from_settings(session)
    try:
        media, path = service.resolve_media_file(media_id)
    except (MediaFilesServiceError, MediaStorageError) as exc:
        logger.warning("Could not deliver media {}: {}", media_id, exc)
        raise HTTPException(status_code=404, detail="Media file not found.") from exc
    return FileResponse(
        path,
        media_type=media.mime_type,
        filename=media.original_filename,
        content_disposition_type="inline",
    )


@router.get("/{media_id}", response_model=MediaRead)
def get_media(media_id: int, session: SessionDep) -> MediaRead:
    return _read_media(MediaFilesService.from_settings(session), media_id)


@router.post("", response_model=MediaRead, status_code=status.HTTP_201_CREATED)
def import_media(
    session: SessionDep,
    file: Annotated[
        UploadFile, File(description="GIF, WebP, MP4, or other supported file")
    ],
    tags: Annotated[list[str], Form(description="Repeat this field for each tag")],
    author: Annotated[str | None, Form()] = None,
    stream_id: Annotated[int | None, Form()] = None,
    emote_name: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
) -> MediaRead:
    """Receive multipart form data, then delegate all media work to the service."""
    temporary: TemporaryUpload | None = None
    try:
        temporary = save_upload(file, settings.active_media_root)
        service = MediaFilesService.from_settings(session)
        media = service.import_media(
            MediaImportRequest(
                source_path=temporary.path,
                original_filename=temporary.original_filename,
                tags=tags,
                author=author,
                stream_id=stream_id,
                emote_name=emote_name,
                title=title,
                description=description,
                source_url=source_url,
            )
        )
        logger.info(
            "Imported media {} from upload {}", media.id, temporary.original_filename
        )
        return _read_media(service, media.id)
    finally:
        if temporary is not None:
            cleanup_upload(temporary)


@router.patch("/{media_id}", response_model=MediaRead)
def update_media(media_id: int, payload: MediaUpdate, session: SessionDep) -> MediaRead:
    values = payload.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(
            status_code=422, detail="Provide at least one field to update."
        )

    service = MediaFilesService.from_settings(session)
    if service.get_media(media_id) is None:
        raise HTTPException(status_code=404, detail="Media not found.")
    service.update_media(
        media_id,
        MediaUpdateRequest(
            provided_fields=frozenset(values),
            **values,
        ),
    )
    return _read_media(service, media_id)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(media_id: int, session: SessionDep) -> Response:
    service = MediaFilesService.from_settings(session)
    if service.get_media(media_id) is None:
        raise HTTPException(status_code=404, detail="Media not found.")
    service.delete_media(media_id)
    logger.info("Deleted media {}", media_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
