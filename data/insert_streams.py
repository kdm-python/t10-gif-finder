import csv
from datetime import datetime

from loguru import logger

from gif_finder.database.database import get_session
from gif_finder.database.models import Stream

DATA_PATH = "data/t10nat_vod_list_full.csv"
START_ROW = 0
END_ROW = 101


def insert_streams(csv_file_path: str, start: int, end: int) -> None:
    """Insert streams from a CSV file into the database."""
    with get_session() as session:
        # If table not empty, abort
        if session.query(Stream).first() is not None:
            logger.warning("Stream table is not empty. Aborting insertion.")
            return
        try:
            logger.info(f"Starting to insert streams from {csv_file_path}")
            with open(csv_file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if reader.line_num < start + 1:  # +1 to account for header row
                        continue
                    if reader.line_num > end:
                        break
                    stream_date = datetime.strptime(row["Date"], "%Y/%m/%d").date()  # noqa: DTZ007
                    # If date exists, do not add
                    if (
                        session.query(Stream).filter_by(stream_date=stream_date).first()
                        is not None
                    ):
                        logger.info(
                            f"Stream with date {stream_date} already exists. Skipping."
                        )
                        continue

                    stream = Stream(
                        stream_date=stream_date,
                        description=row["Youtube link"],
                    )
                    session.add(stream)
            session.commit()
            logger.info("All streams have been successfully inserted.")
        except Exception:  # noqa: BLE001
            logger.exception("Failed to insert streams")


if __name__ == "__main__":
    insert_streams(DATA_PATH, START_ROW, END_ROW)
