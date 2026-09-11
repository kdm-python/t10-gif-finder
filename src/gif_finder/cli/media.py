"""`media` subcommand: add, inspect, view and delete media entries."""

from __future__ import annotations

import argparse

from loguru import logger

from gif_finder.cli.common import (
    DEFAULT_FRAME_RATE,
    media_to_json,
    normalise_tag_values,
    resolve_media_path,
)
from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.media.media_import import import_media
from gif_finder.services.media.media_processor import inspect_media
from gif_finder.services.media.media_service import MediaService


def add_media_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `media` subcommand and its add/inspect/view/delete actions."""
    media_parser = subparsers.add_parser("media", help="Manage media entries.")
    media_actions = media_parser.add_subparsers(dest="media_action", required=True)

    add_parser = media_actions.add_parser(
        "add", aliases=["a"], help="Import a media file."
    )
    add_parser.add_argument("path", help="Path to the media file to import.")
    add_parser.add_argument(
        "-t",
        "--tag",
        dest="tags",
        action="append",
        default=[],
        required=True,
        help="Tag to attach to the imported media. May be specified multiple times.",
    )
    add_parser.add_argument("-a", "--author", help="Optional author name.")
    add_parser.add_argument(
        "-s", "--stream-id", type=int, help="Optional stream ID to attach."
    )
    add_parser.add_argument(
        "-f",
        "--frame-rate",
        type=float,
        default=DEFAULT_FRAME_RATE,
        help="Frame rate to use for timing calculations, especially for WEBP/AVIF media.",
    )
    add_parser.set_defaults(func=run_media_add)

    inspect_parser = media_actions.add_parser(
        "inspect", aliases=["i"], help="Inspect a media file without importing it."
    )
    inspect_parser.add_argument("path", help="Path to the media file to inspect.")
    inspect_parser.add_argument(
        "-f", "--frame-rate", type=float, default=DEFAULT_FRAME_RATE
    )
    inspect_parser.set_defaults(func=run_media_inspect)

    view_parser = media_actions.add_parser(
        "view", aliases=["v"], help="List media entries as JSON."
    )
    view_parser.add_argument("-t", "--tag", help="Filter by tag name.")
    view_parser.add_argument("-a", "--author", help="Filter by author.")
    view_parser.add_argument("-s", "--stream-id", type=int, help="Filter by stream ID.")
    view_parser.set_defaults(func=run_media_view)

    delete_parser = media_actions.add_parser(
        "delete", aliases=["d"], help="Delete a media entry and its stored file."
    )
    delete_parser.add_argument(
        "media_id", type=int, help="ID of the media row to delete."
    )
    delete_parser.set_defaults(func=run_media_delete)


def run_media_add(args: argparse.Namespace) -> None:
    """Import a media file into the database using the service-layer import function."""
    tags = normalise_tag_values(args.tags)
    if not tags:
        raise ValueError("At least one tag is required to add media.")

    path = resolve_media_path(args.path)
    logger.info(
        "Starting media import for {} with tags={} author={} stream_id={} frame_rate={}",
        path,
        tags,
        args.author,
        args.stream_id,
        args.frame_rate,
    )

    create_db_and_tables()
    with get_session() as session:
        media = import_media(
            session,
            path,
            tags=tags,
            author=args.author,
            stream_id=args.stream_id,
            frame_rate=args.frame_rate,
        )
        logger.success("Media imported successfully: {}", media)


def run_media_inspect(args: argparse.Namespace) -> None:
    """Run media inspection only and log the resulting metadata."""
    path = resolve_media_path(args.path)
    logger.info("Inspecting media file: {}", path)

    metadata = inspect_media(path, frame_rate=args.frame_rate)
    logger.success("Inspection complete for {}", path)
    logger.info("Metadata: {}", metadata)


def run_media_view(args: argparse.Namespace) -> None:
    """List media rows, optionally filtered, as JSON."""
    create_db_and_tables()
    with get_session() as session:
        service = MediaService(session)
        rows = service.list(tag=args.tag, author=args.author, stream_id=args.stream_id)
        tags_by_media = service.get_tags_for_media(
            [row.id for row in rows if row.id is not None]
        )
        print(media_to_json(rows, tags_by_media))


def run_media_delete(args: argparse.Namespace) -> None:
    """Delete a media row and its stored file."""
    create_db_and_tables()
    with get_session() as session:
        MediaService(session).delete(args.media_id)
        logger.success("Deleted media {}", args.media_id)
