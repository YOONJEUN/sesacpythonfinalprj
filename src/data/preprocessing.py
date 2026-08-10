# 데이터 전처리 (파생변수 생성도 여긴가?)
import pandas as pd

COLUMN_MAP = {
    "자치구": "district",
    "대여소명": "station_name",
    "기준년월": "stat_mn",
    "대여건수": "rent_cnt",
    "반납건수": "rtn_cnt",
}

def clean_station_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. 컬럼명 통일 (한글 -> 영문, 코드 전체에서 일관되게 참조하기 위함)
    df = df.rename(columns=COLUMN_MAP)

    # 2. 문자열 공백 제거
    for col in ["district", "station_name"]:
        df[col] = df[col].astype(str).str.strip()

    # 3. 기준년월 형식 통일 -> datetime (형식이 섞여 있으면 여기서 NaT로 걸러짐)
    df["stat_mn"] = df["stat_mn"].astype(str).str.strip()

    # 4. 대여/반납건수 숫자형 변환 (콤마 등 방어)
    for col in ["rent_cnt", "rtn_cnt"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    # 5. 결측치 처리
    before = len(df)
    df = df.dropna(subset=["station_name", "rent_cnt", "rtn_cnt"])
    if (dropped := before - len(df)):
        print(f"[전처리] 결측치로 제거된 행: {dropped}건")

    # 6. 음수 이상치 확인
    invalid = df[(df["rent_cnt"] < 0) | (df["rtn_cnt"] < 0)]
    if len(invalid):
        print(f"[전처리] 음수 이상치 {len(invalid)}건 발견 -> 제거")
        df = df[(df["rent_cnt"] >= 0) & (df["rtn_cnt"] >= 0)]

    # 7. 중복 행 제거
    dup_count = df.duplicated(subset=["station_name", "stat_mn"]).sum()
    if dup_count:
        print(f"[전처리] 중복 행 {dup_count}건 발견 -> 첫 값만 유지")
        df = df.drop_duplicates(subset=["station_name", "statMn"], keep="first")

    # 8. 동명이소 대여소 확인 (같은 이름, 다른 자치구)
    name_district_counts = df.groupby("station_name")["district"].nunique()
    ambiguous_names = name_district_counts[name_district_counts > 1]
    if len(ambiguous_names):
        print(f"[전처리] 주의: {len(ambiguous_names)}개 대여소명이 여러 자치구에 걸쳐 존재함")
        print(ambiguous_names.index.tolist())

    return df.sort_values(["district", "station_name"]).reset_index(drop=True)