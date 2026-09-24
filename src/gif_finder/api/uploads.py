"""Safe temporary handling for multipart media uploads."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePath

from fastapi import UploadFile

from gif_finder.logger import logger

MAX_UPLOAD_BYTES = 250 * 1024 * 1024


class UploadError(ValueError):
    """Raised when an uploaded file is unsafe or exceeds the size limit."""


@dataclass(frozen=True)
class TemporaryUpload:
    path: Path
    original_filename: str
    directory: Path


def save_upload(upload: UploadFile, media_root: Path) -> TemporaryUpload:
    """Copy an UploadFile to a private temp directory under the media root."""
    filename = _safe_filename(upload.filename)
    upload_root = media_root / ".uploads"
    upload_root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="upload-", dir=upload_root))
    destination = directory / filename
    bytes_written = 0

    try:
        with destination.open("wb") as target:
            while chunk := upload.file.read(1024 * 1024):
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_BYTES:
                    raise UploadError(
                        f"Upload exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
                    )
                target.write(chunk)
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    finally:
        upload.file.close()

    if bytes_written == 0:
        shutil.rmtree(directory, ignore_errors=True)
        raise UploadError("Uploaded file is empty.")

    logger.info("Received upload filename={} bytes={}", filename, bytes_written)
    return TemporaryUpload(destination, filename, directory)


def cleanup_upload(upload: TemporaryUpload) -> None:
    """Remove the temporary upload after the media workflow completes."""
    shutil.rmtree(upload.directory, ignore_errors=True)


def _safe_filename(value: str | None) -> str:
    if not value:
        raise UploadError("An uploaded file must have a filename.")

    filename = PurePath(value.replace("\\", "/")).name.strip()
    if not filename or filename in {".", ".."} or "\x00" in filename:
        raise UploadError("Uploaded filename is invalid.")
    return filename
