"""`stream` subcommand: add, view and delete streams."""

from __future__ import annotations

import argparse
from datetime import date

from loguru import logger

from gif_finder.cli.common import print_rows
from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.stream import StreamService


def add_stream_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `stream` subcommand and its add/view/delete actions."""
    stream_parser = subparsers.add_parser("stream", help="Manage streams.")
    stream_actions = stream_parser.add_subparsers(dest="stream_action", required=True)

    add_parser = stream_actions.add_parser(
        "add", aliases=["a"], help="Create a stream."
    )
    add_parser.add_argument(
        "-D",
        "--date",
        dest="stream_date",
        type=date.fromisoformat,
        required=True,
        help="Stream date in YYYY-MM-DD format.",
    )
    add_parser.add_argument("-e", "--description", help="Optional stream description.")
    add_parser.set_defaults(func=run_stream_add)

    view_parser = stream_actions.add_parser(
        "view", aliases=["v"], help="List all streams."
    )
    view_parser.set_defaults(func=run_stream_view)

    delete_parser = stream_actions.add_parser(
        "delete", aliases=["d"], help="Delete a stream."
    )
    delete_parser.add_argument(
        "stream_id", type=int, help="ID of the stream to delete."
    )
    delete_parser.set_defaults(func=run_stream_delete)


def run_stream_add(args: argparse.Namespace) -> None:
    """Create a stream."""
    create_db_and_tables()
    with get_session() as session:
        stream = StreamService(session).create(
            stream_date=args.stream_date, description=args.description or ""
        )
        logger.success("Stream created: {}", stream)


def run_stream_view(args: argparse.Namespace) -> None:
    """List all streams."""
    create_db_and_tables()
    with get_session() as session:
        rows = StreamService(session).list()
        print_rows("Streams:", rows, ["id", "stream_date", "description"])


def run_stream_delete(args: argparse.Namespace) -> None:
    """Delete a stream by id."""
    create_db_and_tables()
    with get_session() as session:
        StreamService(session).delete(args.stream_id)
        logger.success("Deleted stream {}", args.stream_id)
