"""`tag` subcommand: add, view and delete tags."""

from __future__ import annotations

import argparse

from loguru import logger

from gif_finder.cli.common import add_json_output_argument, print_rows, rows_to_json
from gif_finder.database.database import create_db_and_tables, get_session
from gif_finder.services.tag import TagService


def add_tag_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Attach the `tag` subcommand and its add/view/delete actions."""
    tag_parser = subparsers.add_parser("tag", help="Manage tags.")
    tag_actions = tag_parser.add_subparsers(dest="tag_action", required=True)

    add_parser = tag_actions.add_parser("add", aliases=["a"], help="Create a tag.")
    add_parser.add_argument("name", help="Name of the tag to create.")
    add_parser.set_defaults(func=run_tag_add)

    view_parser = tag_actions.add_parser("view", aliases=["v"], help="List all tags.")
    add_json_output_argument(view_parser)
    view_parser.set_defaults(func=run_tag_view)

    delete_parser = tag_actions.add_parser(
        "delete", aliases=["d"], help="Delete a tag."
    )
    delete_parser.add_argument("tag_id", type=int, help="ID of the tag to delete.")
    delete_parser.set_defaults(func=run_tag_delete)


def run_tag_add(args: argparse.Namespace) -> None:
    """Create a tag."""
    create_db_and_tables()
    with get_session() as session:
        tag = TagService(session).create(args.name)
        logger.success("Tag created: {}", tag)


def run_tag_view(args: argparse.Namespace) -> None:
    """List all tags."""
    create_db_and_tables()
    with get_session() as session:
        rows = TagService(session).list()
        if args.json:
            print(rows_to_json(rows))
            return
        print_rows("Tags:", rows, ["id", "name"])


def run_tag_delete(args: argparse.Namespace) -> None:
    """Delete a tag by id."""
    create_db_and_tables()
    with get_session() as session:
        TagService(session).delete(args.tag_id)
        logger.success("Deleted tag {}", args.tag_id)
