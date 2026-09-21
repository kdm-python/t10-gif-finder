"""`media` subcommand: add, inspect, view and delete media entries."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from loguru import logger

from gif_finder.cli.common import (
    add_json_output_argument,
    media_to_json,
    normalise_tag_values,
    resolve_media_path,
)
from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.media_files.contracts import MediaImportRequest
from gif_finder.services.media_files.inspector import inspect_media_file
from gif_finder.services.media_files.service import MediaFilesService


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
        "-e", "--emote", help="Optional emote name to attach."
    )
    add_parser.add_argument("--title", help="Optional catalogue title.")
    add_parser.add_argument("--description", help="Optional catalogue description.")
    add_parser.add_argument("--source-url", help="Optional source URL.")
    add_parser.set_defaults(func=run_media_add)

    inspect_parser = media_actions.add_parser(
        "inspect", aliases=["i"], help="Inspect a media file without importing it."
    )
    inspect_parser.add_argument("path", help="Path to the media file to inspect.")
    inspect_parser.set_defaults(func=run_media_inspect)

    view_parser = media_actions.add_parser(
        "view", aliases=["v"], help="List media entries."
    )
    view_parser.add_argument("-t", "--tag", help="Filter by tag name.")
    view_parser.add_argument("-a", "--author", help="Filter by author.")
    view_parser.add_argument("-e", "--emote", help="Filter by emote name.")
    view_parser.add_argument("-s", "--stream-id", type=int, help="Filter by stream ID.")
    view_parser.add_argument("--kind", help="Filter by media kind: image or video.")
    view_parser.add_argument("--format", dest="media_format", help="Filter by format.")
    add_json_output_argument(view_parser)
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
        "Starting media import for {} with tags={} author={} stream_id={}",
        path,
        tags,
        args.author,
        args.stream_id,
    )

    create_db_and_tables()
    with get_session() as session:
        media = MediaFilesService.from_settings(session).import_media(
            MediaImportRequest(
                source_path=path,
                tags=tags,
                author=args.author,
                emote_name=args.emote,
                stream_id=args.stream_id,
                title=args.title,
                description=args.description,
                source_url=args.source_url,
            )
        )
        logger.success("Media imported successfully: {}", media)


def run_media_inspect(args: argparse.Namespace) -> None:
    """Run media inspection only and log the resulting metadata."""
    path = resolve_media_path(args.path)
    logger.info("Inspecting media file: {}", path)

    metadata = inspect_media_file(path)
    logger.success("Inspection complete for {}", path)
    print(json.dumps(asdict(metadata), indent=2, default=str))


def run_media_view(args: argparse.Namespace) -> None:
    """List media rows, optionally filtered."""
    create_db_and_tables()
    with get_session() as session:
        service = MediaFilesService.from_settings(session)
        rows = service.list_media(
            tag=args.tag,
            author=args.author,
            emote_name=args.emote,
            stream_id=args.stream_id,
            media_kind=args.kind,
            media_format=args.media_format,
        )
        tags_by_media = service.get_tags_for_media(
            [row.id for row in rows if row.id is not None]
        )
        if args.json:
            print(media_to_json(rows, tags_by_media))
            return

        print("Media:")
        if not rows:
            print("  (none)")
            return
        print("  id | format | dimensions | duration_ms | author | tags | filename")
        for row in rows:
            dimensions = f"{row.width}x{row.height}"
            tags = ", ".join(tags_by_media.get(row.id, []))
            print(
                "  "
                f"{row.id} | {row.format} | {dimensions} | {row.duration_ms} | "
                f"{row.author or ''} | {tags} | {row.original_filename}"
            )


def run_media_delete(args: argparse.Namespace) -> None:
    """Delete a media row and its stored file."""
    create_db_and_tables()
    with get_session() as session:
        MediaFilesService.from_settings(session).delete_media(args.media_id)
        logger.success("Deleted media {}", args.media_id)
