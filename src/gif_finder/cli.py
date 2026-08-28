"""Command-line helpers for testing GIF import and inspection workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.emote import EmoteService
from gif_finder.services.media.media_import import import_media
from gif_finder.services.media.media_processor import inspect_media
from gif_finder.services.stream import StreamService
from gif_finder.services.tag import TagService

DEFAULT_FRAME_RATE = 24.0


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


def _normalise_tag_values(raw_tags: list[str] | tuple[str, ...] | None) -> list[str]:
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


def _resolve_media_path(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")
    return path


def run_inspect(path_text: str, frame_rate: float | None = None) -> None:
    """Run media inspection only and log the resulting metadata."""
    path = _resolve_media_path(path_text)
    logger.info("Inspecting media file: {}", path)

    metadata = inspect_media(path, frame_rate=frame_rate or DEFAULT_FRAME_RATE)
    logger.success("Inspection complete for {}", path)
    logger.info("Metadata: {}", metadata)


def run_import(
    path_text: str,
    tags: list[str],
    *,
    author: str | None = None,
    stream_id: int | None = None,
    frame_rate: float | None = DEFAULT_FRAME_RATE,
) -> None:
    """Import a media file into the database using the service-layer import function."""
    if not tags:
        raise ValueError("At least one tag is required for import mode.")

    path = _resolve_media_path(path_text)
    logger.info(
        "Starting media import for {} with tags={} author={} stream_id={} frame_rate={}",
        path,
        tags,
        author,
        stream_id,
        frame_rate,
    )

    create_db_and_tables()
    with get_session() as session:
        media = import_media(
            session,
            path,
            tags=tags,
            author=author,
            stream_id=stream_id,
            frame_rate=frame_rate,
        )
        logger.success("Media imported successfully: {}", media)


def _print_rows(title: str, rows: list[object], columns: list[str]) -> None:
    """Pretty-print a list of rows for CLI inspection."""
    print(title)
    if not rows:
        print("  (none)")
        return

    print("  " + " | ".join(columns))
    for row in rows:
        values = [str(getattr(row, column, "")) for column in columns]
        print("  " + " | ".join(values))


def run_show(kind: str) -> None:
    """List all tags, streams or emotes in the database."""
    create_db_and_tables()
    with get_session() as session:
        if kind == "tags":
            rows = TagService(session).list()
            _print_rows("Tags:", rows, ["id", "name"])
            return
        if kind == "streams":
            rows = StreamService(session).list()
            _print_rows("Streams:", rows, ["id", "stream_date", "description"])
            return
        if kind == "emotes":
            rows = EmoteService(session).list()
            _print_rows("Emotes:", rows, ["id", "name", "media_id"])
            return

        raise ValueError(f"Unsupported show target: {kind}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "GIF Finder testing CLI. Use import mode to persist media or --inspect to "
            "inspect metadata only."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Path to the media file to import. Required unless --inspect is used.",
    )
    parser.add_argument(
        "tags",
        nargs="*",
        help=(
            "One or more tags to apply on import. Can be passed as positional args or "
            "repeated with --tag. Comma-separated values are also accepted."
        ),
    )
    parser.add_argument(
        "-t",
        "--tag",
        dest="tag_args",
        action="append",
        default=[],
        help="Tag to attach to the imported media. May be specified multiple times.",
    )
    parser.add_argument(
        "--inspect",
        metavar="PATH",
        help="Inspect a single media file and log the metadata without adding it to the database.",
    )
    parser.add_argument(
        "--show",
        choices=("tags", "streams", "emotes"),
        help="List all tags, streams or emotes and print their IDs for manual testing.",
    )
    parser.add_argument(
        "--author",
        help="Optional author name to store along with the imported media.",
    )
    parser.add_argument(
        "--stream-id",
        type=int,
        help="Optional stream ID to attach to the imported media.",
    )
    parser.add_argument(
        "--frame-rate",
        type=float,
        default=DEFAULT_FRAME_RATE,
        help="Frame rate to use for timing calculations, especially for WEBP/AVIF media.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point used by the CLI and project script."""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.show:
            run_show(args.show)
            return 0

        if args.inspect:
            run_inspect(args.inspect, frame_rate=args.frame_rate)
            return 0

        if not args.path:
            parser.error("A media path is required unless --inspect or --show is used.")

        combined_tags = _normalise_tag_values(args.tags + args.tag_args)
        if not combined_tags:
            parser.error(
                "At least one tag is required for import mode. Use positional tags or --tag."
            )

        run_import(
            args.path,
            combined_tags,
            author=args.author,
            stream_id=args.stream_id,
            frame_rate=args.frame_rate,
        )
        return 0
    except Exception as exc:  # pragma: no cover - CLI safety net
        logger.exception("CLI command failed: {}", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
