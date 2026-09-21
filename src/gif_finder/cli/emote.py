"""`emote` subcommand: add, view and delete emotes."""

from __future__ import annotations

import argparse

from loguru import logger

from gif_finder.cli.common import add_json_output_argument, print_rows, rows_to_json
from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.emote import EmoteService


def add_emote_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `emote` subcommand and its add/view/delete actions."""
    emote_parser = subparsers.add_parser("emote", help="Manage emotes.")
    emote_actions = emote_parser.add_subparsers(dest="emote_action", required=True)

    add_parser = emote_actions.add_parser("add", aliases=["a"], help="Create an emote.")
    add_parser.add_argument("name", help="Name of the emote to create.")
    add_parser.add_argument(
        "-m", "--media-id", type=int, help="Optional media ID to assign the emote to."
    )
    add_parser.set_defaults(func=run_emote_add)

    view_parser = emote_actions.add_parser(
        "view", aliases=["v"], help="List all emotes."
    )
    add_json_output_argument(view_parser)
    view_parser.set_defaults(func=run_emote_view)

    delete_parser = emote_actions.add_parser(
        "delete", aliases=["d"], help="Delete an emote."
    )
    delete_parser.add_argument("emote_id", type=int, help="ID of the emote to delete.")
    delete_parser.set_defaults(func=run_emote_delete)


def run_emote_add(args: argparse.Namespace) -> None:
    """Create an emote, optionally assigning it to a media row."""
    create_db_and_tables()
    with get_session() as session:
        emote = EmoteService(session).create(name=args.name, media_id=args.media_id)
        logger.success("Emote created: {}", emote)


def run_emote_view(args: argparse.Namespace) -> None:
    """List all emotes."""
    create_db_and_tables()
    with get_session() as session:
        rows = EmoteService(session).list()
        if args.json:
            print(rows_to_json(rows))
            return
        print_rows("Emotes:", rows, ["id", "name"])


def run_emote_delete(args: argparse.Namespace) -> None:
    """Delete an emote by id."""
    create_db_and_tables()
    with get_session() as session:
        EmoteService(session).delete(args.emote_id)
        logger.success("Deleted emote {}", args.emote_id)
