"""
Config for environment variables and other settings.
"""

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Settings for the application."""

    giffinder_env: Literal["development", "production", "test"] = "development"
    giffinder_database_url: str
    giffinder_media_root: str
    giffinder_test_database_url: str
    giffinder_test_media_root: str
    log_level: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def active_database_url(self) -> str:
        """Return the database URL for the selected runtime environment."""
        if self.giffinder_env in {"development", "test"}:
            return self.giffinder_test_database_url
        return self.giffinder_database_url

    @property
    def active_media_root(self) -> Path:
        """Return the media root paired with the selected database."""
        if self.giffinder_env in {"development", "test"}:
            configured_root = self.giffinder_test_media_root
        else:
            configured_root = self.giffinder_media_root

        if not configured_root.strip():
            raise ValueError(
                f"A media root must be configured for {self.giffinder_env} mode."
            )
        return Path(configured_root).expanduser()


settings = Settings()


# class Settings(BaseSettings):
#     """Settings for the application."""

#     test_database_url: str
#     postgres_url: str
#     frame_rate_default: float
#     media_path: str

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"


# settings = Settings()
