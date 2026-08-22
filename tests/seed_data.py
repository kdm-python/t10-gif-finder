"""Seed the GIF Finder database from static JSON fixtures."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlmodel import Session

from gif_finder.database.database import create_db_and_tables, engine
from gif_finder.database.models import Emote, EmoteMedia, Media, MediaTag, Stream, Tag

SEED_DATA_DIR = Path(__file__).resolve().parents[1] / "tests/seed_data"


def _seed_paths() -> dict[str, Path]:
    return {
        "streams": SEED_DATA_DIR / "streams.json",
        "tags": SEED_DATA_DIR / "tags.json",
        "media": SEED_DATA_DIR / "media.json",
        "emotes": SEED_DATA_DIR / "emotes.json",
    }


def _load_json_records(filename: str) -> list[dict[str, Any]]:
    file_path = _seed_paths()[Path(filename).stem]
    logger.info("Loading seed records from {path}", path=file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Seed file does not exist: {file_path}")

    with file_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        raise TypeError(
            f"Expected a JSON list in {file_path}, got {type(payload).__name__}"
        )

    logger.info(
        "Loaded {count} seed records from {file}",
        count=len(payload),
        file=file_path.name,
    )
    return payload


def _normalize_seed_value(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)

    if "stream_date" in normalized and normalized["stream_date"] is not None:
        normalized["stream_date"] = date.fromisoformat(str(normalized["stream_date"]))

    if "imported_at" in normalized and normalized["imported_at"] is not None:
        normalized["imported_at"] = datetime.fromisoformat(
            str(normalized["imported_at"])
        )

    return normalized


def database_has_data() -> bool:
    """Return True if any application table contains at least one row."""
    with Session(engine) as session:
        for table_name in ("stream", "tag", "media", "emote", "mediatag", "emotemedia"):
            row_count = session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar_one()
            if row_count > 0:
                logger.warning(
                    "Database is not empty: table '{table}' already contains {count} row(s).",
                    table=table_name,
                    count=row_count,
                )
                return True

    logger.info("Database contains no application data.")
    return False


def _seed_streams(records: list[dict[str, Any]]) -> None:
    logger.info("Seeding {count} streams.", count=len(records))
    with Session(engine) as session:
        session.add_all(Stream(**_normalize_seed_value(record)) for record in records)
        session.commit()
    logger.success("Completed stream seeding.")


def _seed_tags(records: list[dict[str, Any]]) -> None:
    logger.info("Seeding {count} tags.", count=len(records))
    with Session(engine) as session:
        session.add_all(Tag(**_normalize_seed_value(record)) for record in records)
        session.commit()
    logger.success("Completed tag seeding.")


def _seed_media(records: list[dict[str, Any]]) -> None:
    logger.info("Seeding {count} media items.", count=len(records))
    media_rows: list[Media] = []
    media_tag_rows: list[MediaTag] = []

    for record in records:
        normalized = _normalize_seed_value(record)
        media_rows.append(
            Media(
                **{key: value for key, value in normalized.items() if key != "tag_ids"}
            )
        )

        for tag_id in normalized.get("tag_ids", []):
            media_tag_rows.append(MediaTag(media_id=normalized["id"], tag_id=tag_id))

    with Session(engine) as session:
        session.add_all(media_rows)
        session.commit()

        if media_tag_rows:
            session.add_all(media_tag_rows)
            session.commit()

    logger.success("Completed media and media-tag seeding.")


def _seed_emotes(records: list[dict[str, Any]]) -> None:
    logger.info("Seeding {count} emotes.", count=len(records))
    emote_rows: list[Emote] = []
    emote_media_rows: list[EmoteMedia] = []

    for record in records:
        normalized = _normalize_seed_value(record)
        emote_rows.append(
            Emote(
                id=normalized["id"],
                name=normalized["name"],
                media_id=normalized["media_id"],
            )
        )

        for media_id in normalized.get("media_ids", []):
            emote_media_rows.append(
                EmoteMedia(emote_id=normalized["id"], media_id=media_id)
            )

    with Session(engine) as session:
        session.add_all(emote_rows)
        session.commit()
        if emote_media_rows:
            session.add_all(emote_media_rows)
            session.commit()

    logger.success("Completed emote and emote-media seeding.")


def seed_data() -> bool:
    """Seed the database when it is empty, and abort when it already contains data."""
    logger.info("Starting the seed process.")

    try:
        create_db_and_tables()
        logger.info("Ensured database tables exist.")
    except Exception as exc:
        logger.exception("Failed to create tables before seeding: {exc}", exc=exc)
        return False

    if database_has_data():
        logger.warning("Seed aborted because the database is not empty.")
        return False

    try:
        streams = _load_json_records("streams.json")
        tags = _load_json_records("tags.json")
        media = _load_json_records("media.json")
        emotes = _load_json_records("emotes.json")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("Unable to load seed files: {exc}", exc=exc)
        return False

    try:
        _seed_streams(streams)
        _seed_tags(tags)
        _seed_media(media)
        _seed_emotes(emotes)
    except Exception as exc:
        logger.exception("Seed operation failed while writing data: {exc}", exc=exc)
        return False

    logger.success("Seed operation completed successfully.")
    return True


if __name__ == "__main__":
    seed_data()
