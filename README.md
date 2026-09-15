# GIF Finder

GIF Finder is a Python project for importing, organizing, and searching animated media files such as GIFs and related assets. It stores metadata in a database and exposes both a command-line interface and a small FastAPI application for managing media, tags, streams, and emotes.

## Features

- Import media files and capture technical metadata such as size, dimensions, animation details, and frame rate
- Organize media using tags, streams, and emotes
- List, inspect, and delete records from the CLI
- Persist data with SQLModel / SQLite or PostgreSQL configuration

## Project structure

- `src/gif_finder/cli` — CLI commands for media, tags, streams, and emotes
- `src/gif_finder/api` — API routes
- `src/gif_finder/database` — database models and session setup
- `src/gif_finder/services` — processing and storage logic
- `tests` — smoke and service tests

## Requirements

- Python 3.13+
- Dependencies managed via `pyproject.toml`

## Setup

1. Create a virtual environment and install dependencies.
2. Configure your environment variables in a `.env` file, including the values used by `Settings` such as:
   - `test_database_url`
   - `postgres_url`
   - `sqlite_url`
   - `frame_rate_default`
   - `media_path`

Example:

```bash
uv sync
uv run gif-finder --help
```

## Usage

View the available commands:

```bash
gif-finder --help
```

Examples:

```bash
gif-finder media add ./path/to/file.gif --tag funny --tag reaction
gif-finder media view
gif-finder tag add meme
gif-finder stream view
```

## Notes

This project is focused on a local media catalog workflow. It is especially useful for collecting and labeling GIFs and related clips before later reuse in tools or applications.
