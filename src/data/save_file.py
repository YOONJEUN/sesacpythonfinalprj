"""Call the rental API and save selected response columns as CSV."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from src.api.bike_api import get_bike_rental_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RENTAL_COLUMNS = ["RENT_DT", "RENT_ID", "RENT_NM", "RTN_DT", "RTN_ID", "RTN_NM", "USE_MIN", "USE_DST", "SEX_CD"]


def save_rental_week(start_date: str = "2026-04-01", days: int = 7, page_size: int = 1000) -> Path:
    """Fetch a requested week from the API and save only RENTAL_COLUMNS to CSV."""
    if days < 1:
        raise ValueError("days must be at least 1")
    first_day = date.fromisoformat(start_date)
    records: list[dict] = []
    for offset in range(days):
        request_date = (first_day + timedelta(days=offset)).isoformat()
        for hour in range(24):
            start = 1
            while True:
                payload = get_bike_rental_data(start, start + page_size - 1, request_date, hour)
                rows = payload["rentData"].get("row", [])
                records.extend({column: row.get(column) for column in RENTAL_COLUMNS} for row in rows)
                if len(rows) < page_size:
                    break
                start += page_size
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DATA_DIR / f"SeoulBikeRental_{first_day:%Y%m%d}_{days}days.csv"
    pd.DataFrame(records, columns=RENTAL_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")
    return path
