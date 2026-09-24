"""Consistent HTTP responses for known application failures."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gif_finder.database.database import DatabaseUnavailableError
from gif_finder.logger import logger
from gif_finder.services.media_files.ffprobe import MediaProbeError
from gif_finder.services.media_files.repository import MediaRepositoryError
from gif_finder.services.media_files.service import MediaFilesServiceError
from gif_finder.services.media_files.storage import MediaStorageError
from gif_finder.api.uploads import UploadError


def register_exception_handlers(app: FastAPI) -> None:
    """Install narrow error mappings and a safe final exception boundary."""

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable(_: Request, exc: DatabaseUnavailableError):
        logger.error("Database unavailable: {}", exc)
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(
        MediaFilesServiceError
    )
    @app.exception_handler(MediaRepositoryError)
    @app.exception_handler(MediaStorageError)
    @app.exception_handler(MediaProbeError)
    @app.exception_handler(UploadError)
    async def invalid_media_request(_: Request, exc: Exception):
        logger.warning("Invalid media request: {}", exc)
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def invalid_request(_: Request, exc: ValueError):
        logger.warning("Invalid request: {}", exc)
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_exception(_: Request, exc: Exception):
        logger.exception("Unhandled API exception")
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})
