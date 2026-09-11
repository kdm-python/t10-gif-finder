from fastapi import APIRouter, Depends, HTTPException

from gif_finder.config import settings
from gif_finder.database.database import get_session

router = APIRouter(prefix="/gifs", tags=["GIFs"])
