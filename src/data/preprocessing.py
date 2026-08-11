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
