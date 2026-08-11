import pandas as pd

COLUMN_MAP = {
    "자치구": "district", 
    "대여소명": "station_name", 
    "기준년월": "stat_mn", 
    "대여건수": "rent_cnt", 
    "반납건수": "rtn_cnt"
}

def clean_station_df(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(columns=COLUMN_MAP).copy()
    required = set(COLUMN_MAP.values())
    missing = required.difference(result.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    for col in ("district", "station_name", "stat_mn"):
        result[col] = result[col].astype("string").str.strip()
    for col in ("rent_cnt", "rtn_cnt"):
        result[col] = pd.to_numeric(result[col].astype("string").str.replace(",", "", regex=False), errors="coerce")
    result = result.dropna(subset=list(required))
    result = result[(result["rent_cnt"] >= 0) & (result["rtn_cnt"] >= 0)]
    return result.drop_duplicates(["district", "station_name", "stat_mn"]).reset_index(drop=True)


def add_imbalance(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["imbalance"] = result["rent_cnt"] - result["rtn_cnt"]
    result["imbalance_abs"] = result["imbalance"].abs()
    return result

def preprocess_rental_data(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result.columns = [col.lower() for col in result.columns]

    result["rent_dt"] = pd.to_datetime(result["rent_dt"], errors="coerce")
    result["rtn_dt"] = pd.to_datetime(result["rtn_dt"], errors="coerce")
    result["use_min"] = pd.to_numeric(result["use_min"], errors="coerce")
    result["use_dst"] = pd.to_numeric(result["use_dst"], errors="coerce")

    result["rent_year"] = result["rent_dt"].dt.year
    result["rent_month"] = result["rent_dt"].dt.month
    result["rent_day"] = result["rent_dt"].dt.day
    result["rent_hour"] = result["rent_dt"].dt.hour
    result["rtn_hour"] = result["rtn_dt"].dt.hour
    
    return result.dropna(subset=["rent_dt", "rent_id", "rtn_id", "use_min", "use_dst"]).reset_index(drop=True)




STATION_LOCATION_COLUMN_MAP = {
    "대여소_ID": "station_id",
    "주소1": "addr1",
    "주소2": "addr2",
    "위도": "lat",
    "경도": "lon",
}

def preprocess_station_location(df: pd.DataFrame) -> pd.DataFrame:
    """대여소 위치 데이터의 컬럼명을 정리하고 결측치를 제거해, 지도/join에 바로 쓸 수 있는 형태로 만듭니다."""
    result = df.rename(columns=STATION_LOCATION_COLUMN_MAP).copy()

    result["lat"] = pd.to_numeric(result["lat"], errors="coerce")
    result["lon"] = pd.to_numeric(result["lon"], errors="coerce")
    result["station_id"] = result["station_id"].astype(str).str.strip()

    result = result.dropna(subset=["station_id", "lat", "lon"])
    result = result[
        result["lat"].between(37.0, 38.0) & result["lon"].between(126.0, 128.0)
    ]

    return result.drop_duplicates(subset="station_id").reset_index(drop=True)
