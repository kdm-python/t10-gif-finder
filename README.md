# T10Nat GIF Finder

The streamer T10Nat has an endless number of GIFs and clips that I want to organise into a single database. This application is intended to categorise and sort them all so they can be stored securely, queried and retrieved. The application is in its early stages, the next step will be to produce a (probably Next JS) frontend to host to allow others to upload to some sort of central database.

GIF Finder is a local, CLI-first catalogue for GIF, WebP, MP4, and other
`ffprobe`-supported visual media. It inspects each file, stores its technical
metadata and catalogue data in PostgreSQL, and copies the file into a
content-addressed media store. A web application is not part of the project at
present.

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL, with the databases created before running the application
- FFmpeg, with `ffprobe` available on `PATH`

Pillow is installed as a Python dependency and supplements `ffprobe` with image
facts where useful.

## Install and configure

Install the project dependencies:

```bash
uv sync
```

Create the two PostgreSQL databases (adjust the PostgreSQL role as needed):

```bash
createdb giffinder
createdb giffinder_test
```

Copy the example configuration and fill in the connection URLs and absolute
media-store paths:

```bash
cp .env.example .env
```

```dotenv
# development and test use the isolated test database and media root
GIFFINDER_ENV=development

GIFFINDER_DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/giffinder
GIFFINDER_MEDIA_ROOT=/absolute/path/to/giffinder-media

GIFFINDER_TEST_DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/giffinder_test
GIFFINDER_TEST_MEDIA_ROOT=/absolute/path/to/gif-finder/tests/.runtime-media

LOG_LEVEL=debug
```

All five settings are required, even when only one environment is active.
`development` and `test` select `GIFFINDER_TEST_DATABASE_URL` and
`GIFFINDER_TEST_MEDIA_ROOT`; `production` selects the non-test values. Keep the
two media roots separate: imports copy files into the active root and deleting
a media record removes its stored file.

The application creates missing tables in the selected existing database. It
does not create PostgreSQL databases; a missing or unreachable database is
reported in the CLI log and the command exits unsuccessfully.

## CLI usage

Run commands through `uv` during development:

```bash
uv run gif-finder --help
```

Or, after activating the environment, use `gif-finder` directly. The current
commands manage media, tags, streams, and emotes:

```bash
# Inspect without copying the file or writing to PostgreSQL.
uv run gif-finder media inspect ./clip.gif

# Import a file. At least one tag is required.
uv run gif-finder media add ./clip.webp --tag funny --tag reaction \
  --author "Example author" --title "Surprised reaction"

# MP4 files are inspected with ffprobe too.
uv run gif-finder media add ./clip.mp4 --tag highlight

# List and filter the catalogue.
uv run gif-finder media view
uv run gif-finder media view --tag funny --format webp
uv run gif-finder media view --kind video --json | jq .

# Manage supporting records.
uv run gif-finder tag add meme
uv run gif-finder stream add --date 2026-09-21 --description "Evening stream"
uv run gif-finder emote add pog
uv run gif-finder tag view --json > tags.json
```

`media view`, `tag view`, `stream view`, and `emote view` accept `--json` for
machine-readable output. Logs are written to stderr, so JSON on stdout can be
piped to `jq` or redirected safely.

Use `--help` at any level for the complete option list:

```bash
uv run gif-finder media add --help
uv run gif-finder media view --help
```

## Tests

Tests use PostgreSQL rather than SQLite because the schema uses PostgreSQL
features such as JSONB. They require a reachable `giffinder_test` database
matching `GIFFINDER_TEST_DATABASE_URL` and will clear its application tables
between tests. Never point this variable at the production database.

```bash
uv run pytest -q
```

Small GIF, WebP, and MP4 fixtures live under `tests/fixtures`. Runtime test
media belongs in `tests/.runtime-media`, which is ignored by Git.
