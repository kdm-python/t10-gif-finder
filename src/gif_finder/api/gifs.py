"""API Endpoints for GIFs."""

from fastapi import APIRouter, Depends, HTTPException

from gif_finder.database.database import get_session
from gif_finder.database.models import Media, MediaMetadata

router = APIRouter(prefix="/gifs", tags=["GIFs"])
