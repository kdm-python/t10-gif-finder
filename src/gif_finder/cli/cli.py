"""GIF Finder command-line interface.

Usage:
    gif-finder media add PATH --tag TAG [--tag TAG ...] [--author NAME] [--emote NAME] [--stream-id ID]
    gif-finder media inspect PATH
    gif-finder media view [--tag NAME] [--author NAME] [--emote NAME] [--stream-id ID] [--json]
    gif-finder media delete MEDIA_ID

    gif-finder tag add NAME
    gif-finder tag view [--json]
    gif-finder tag delete TAG_ID

    gif-finder stream add --date YYYY-MM-DD [--description TEXT]
    gif-finder stream view [--json]
    gif-finder stream delete STREAM_ID

    gif-finder emote add NAME [--media-id ID]
    gif-finder emote view [--json]
    gif-finder emote delete EMOTE_ID

Each action also accepts a single-letter alias in place of its full name,
e.g. `gif-finder media a ...`, `gif-finder tag d 3`, `gif-finder stream v`.

Entity subcommands:
    media   Import, inspect, list and delete media entries.
    tag     Create, list and delete tags.
    stream  Create, list and delete streams.
    emote   Create, list and delete emotes.
"""

from __future__ import annotations

import argparse

from loguru import logger

from gif_finder.cli.common import configure_logging
from gif_finder.cli.emote import add_emote_subparser
from gif_finder.cli.media import add_media_subparser
from gif_finder.cli.stream import add_stream_subparser
from gif_finder.cli.tag import add_tag_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GIF Finder CLI for managing media, tags, streams and emotes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="entity", required=True)

    add_media_subparser(subparsers)
    add_tag_subparser(subparsers)
    add_stream_subparser(subparsers)
    add_emote_subparser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point used by the CLI and project script."""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.func(args)
        return 0
    except Exception as exc:  # pragma: no cover - CLI safety net
        logger.exception("CLI command failed: {}", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
