"""Call the rental API and save selected response columns as CSV."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.api.bike_api import get_bike_rental_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RENTAL_COLUMNS = ["RENT_DT", "RENT_ID", "RENT_NM", "RTN_DT", "RTN_ID", "RTN_NM", "USE_MIN", "USE_DST", "SEX_CD", "RENT_STATION_ID", "RETURN_STATION_ID"]


def save_rental_week(start_date: str = "2026-04-01", days: int = 7, page_size: int = 1000) -> Path:
    if days < 1:
        raise ValueError("days must be at least 1")
    first_day = date.fromisoformat(start_date)
    records: list[dict] = []

    # 전체 (일 x 시간) 조합에 대한 진행률 표시줄
    progress_bar = tqdm(total=days * 24, desc="수집 중", unit="시간")

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

            # 한 시간대(=한 번의 while loop) 완료될 때마다 진행률 갱신 + 누적 건수 표시
            progress_bar.set_postfix(날짜=request_date, 시=hour, 누적건수=len(records))
            progress_bar.update(1)
            
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DATA_DIR / f"SeoulBikeRental_{first_day:%Y%m%d}_{days}days.csv"
    pd.DataFrame(records, columns=RENTAL_COLUMNS).to_csv(path, index=False, encoding="utf-8-sig")
    # return path

def save_processed_data(df : pd.DataFrame, filename : str) -> Path:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DATA_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    # return path

if __name__ == "__main__": 
    save_rental_week(start_date="2026-04-01", days=7)