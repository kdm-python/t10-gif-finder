"""Main entry point for the GIF Finder application."""

from loguru import logger

from gif_finder.database.database import create_db_and_tables

if __name__ == "__main__":
    logger.info("Creating database and tables...")
    create_db_and_tables()
