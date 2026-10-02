"""FastAPI application factory and router registration."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gif_finder.api.errors import register_exception_handlers
from gif_finder.api.routers import emotes, media, streams, tags, twitch
from gif_finder.config import settings
from gif_finder.database.database import create_db_and_tables
from gif_finder.logger import configure_api_logging, logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_api_logging()
    logger.info("Starting GIF Finder API in {} mode", settings.giffinder_env)
    create_db_and_tables()
    logger.info("Database is ready")
    yield
    logger.info("Stopping GIF Finder API")


app = FastAPI(
    title="GIF Finder API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tags.router)
app.include_router(emotes.router)
app.include_router(streams.router)
app.include_router(media.router)
app.include_router(twitch.router)
register_exception_handlers(app)

# Keep the small, dependency-free client alongside the API for local use.
# ``html=True`` makes /app/ serve frontend/index.html.
frontend_directory = Path(__file__).resolve().parents[3] / "frontend"
app.mount("/app", StaticFiles(directory=frontend_directory, html=True), name="frontend")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Small unauthenticated readiness endpoint for local development."""
    return {"status": "ok"}
