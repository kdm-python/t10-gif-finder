"""
Config for environment variables and other settings.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Settings for the application."""

    test_database_url: str

    postgres_url: str
    sqlite_url: str

    frame_rate_default: float
    media_path: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
