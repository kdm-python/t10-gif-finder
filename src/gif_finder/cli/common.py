"""Shared CLI helpers used across the media/tag/stream/emote subcommands."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from loguru import logger

def configure_logging() -> None:
    """Configure a consistent log output format for CLI diagnostics."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>: <level>{message}</level>"
        ),
        level="DEBUG",
        enqueue=True,
    )


def normalise_tag_values(raw_tags: list[str] | tuple[str, ...] | None) -> list[str]:
    """Expand comma-separated tags and discard blanks."""
    if not raw_tags:
        return []

    tags: list[str] = []
    for value in raw_tags:
        for tag in str(value).split(","):
            tag = tag.strip()
            if tag:
                tags.append(tag)
    return tags


def resolve_media_path(path_text: str) -> Path:
    """Expand and validate a user-supplied media file path."""
    path = Path(path_text).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")
    return path


def print_rows(title: str, rows: list[object], columns: list[str]) -> None:
    """Pretty-print a list of rows as a simple aligned table."""
    print(title)
    if not rows:
        print("  (none)")
        return

    print("  " + " | ".join(columns))
    for row in rows:
        values = [str(getattr(row, column, "")) for column in columns]
        print("  " + " | ".join(values))


def add_json_output_argument(parser: argparse.ArgumentParser) -> None:
    """Add consistent machine-readable output support to a listing command."""
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print records as JSON to stdout for piping or saving.",
    )


def rows_to_json(rows: list[object]) -> str:
    """Serialise SQLModel/Pydantic rows as a JSON array."""
    payload = [
        row.model_dump() if hasattr(row, "model_dump") else row for row in rows
    ]
    return json.dumps(payload, indent=2, default=_json_default)


def media_to_json(media_rows: list[object], tags_by_media: dict[int, list[str]]) -> str:
    """Serialise media rows with attached tag names as pretty JSON."""
    payload = []
    for media in media_rows:
        record = media.model_dump()
        record["tags"] = tags_by_media.get(media.id, [])
        payload.append(record)
    return json.dumps(payload, indent=2, default=_json_default)


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
