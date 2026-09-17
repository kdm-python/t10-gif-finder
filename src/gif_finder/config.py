"""
Config for environment variables and other settings.
"""

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Settings for the application."""

    giffinder_env: str
    giffinder_database_url: str
    giffinder_media_root: str
    giffinder_test_database_url: str
    giffinder_test_media_root: str
    log_level: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
