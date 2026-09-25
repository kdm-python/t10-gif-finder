"""
Insert streams from a CSV file into the database.

This script reads a CSV file containing stream information and inserts the streams into the database.
It skips rows without a date and avoids inserting duplicate streams based on the stream date.

USAGE:
    # From parent app directory
    uv run data/insert_streams.py -> Uses the default provided file
    uv run data/insert_streams.py <csv_file_path> <start_row> <end_row> -> Custom file / range of rows
    # Custom file must have a "Date" column and a "Youtube link" column as the first two headers
"""

import csv
from datetime import datetime

from loguru import logger

from gif_finder.database.database import get_session
from gif_finder.database.models import Stream

DATA_PATH = "data/t10nat_vod_list_full.csv"
START_ROW = 0
END_ROW = 1000  # Adjust as needed


def insert_streams(csv_file_path: str, start: int, end: int) -> None:
    """Insert streams from a CSV file into the database."""
    with get_session() as session:
        try:
            logger.info(f"Starting to insert streams from {csv_file_path}")
            with open(csv_file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                count = 0
                for row in reader:
                    if reader.line_num < start + 1:  # +1 to account for header row
                        continue
                    if reader.line_num > end:
                        break

                    # If no date, skip the row
                    if not row["Date"]:
                        logger.warning(f"Row {reader.line_num} has no date. Skipping.")
                        continue

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
                    count += 1
            session.commit()
            logger.info(
                f"All streams have been successfully inserted. Total inserted: {count}"
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to insert streams")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 4:
        _, data_path, start_row, end_row = sys.argv
        insert_streams(data_path, int(start_row), int(end_row))
    else:
        insert_streams(DATA_PATH, START_ROW, END_ROW)
