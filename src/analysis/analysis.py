# 집계, 통계, 지표 계산 등 분석 로직
# 실제 데이터 분석

import pandas as pd

def add_imbalance(df: pd.DataFrame) -> pd.DataFrame: 
    imbalance_df = df.copy()
    imbalance_df["imbalance"] = imbalance_df["rent_cnt"] - imbalance_df["rtn_cnt"]
    imbalance_df["imbalance_abs"] = imbalance_df["imbalance"].abs()
    return imbalance_df

def add_year_month(df: pd.DataFrame) -> pd.DataFrame: 
    year_month_df = df.copy()
    date = pd.to_datetime(df["stat_mn"].astype(str), format="%Y%m")
    year_month_df["year"] = date.dt.year
    year_month_df["month"] = date.dt.month
    return year_month_df