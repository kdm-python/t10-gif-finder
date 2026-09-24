"""Shared Loguru setup for the HTTP API."""

from __future__ import annotations

import sys

from loguru import logger as _logger

from gif_finder.config import settings

logger = _logger.bind(component="api")


def configure_api_logging() -> None:
    """Configure concise, structured-enough diagnostics for API processes."""
    _logger.remove()
    _logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        enqueue=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan> | <level>{message}</level>"
        ),
    )
