# 최종 Streamlit 화면
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import koreanize_matplotlib
from src.data.loader import (load_csv,)
from src.data.preprocessing import (clean_station_df,)
from src.analysis.analysis import (add_imbalance, add_year_month,)

filenames = ["SeoulBikeStationUseInfo_2601to2606.csv", "SeoulBikeStationUseInfo_2507to2512.csv"]
raw_station_df = load_csv(filenames) # 불러오기

station_df = clean_station_df(raw_station_df) # 전처리
station_df = add_imbalance(station_df).copy() # 파생변수 생성
station_df = add_year_month(station_df).copy()
print(station_df.head())

print(station_df.groupby("district")["imbalance_abs"].mean().nlargest(10))
print(station_df.groupby(["year", "month"])["imbalance_abs"].mean().nlargest(10)) # 이거 기준으로 2026년 4월 한달을 선정
# 이제 rentdata 2026년 4월 







district_result = (
    station_df
    .groupby("district")
    .agg(
        총대여건수=("rent_cnt", "sum"),
        총반납건수=("rtn_cnt", "sum"),
        총불균형=("imbalance", "sum"),
        평균불균형=("imbalance", "mean"),
        평균절대불균형=("imbalance_abs", "mean")
    )
    .reset_index()
)
# print(len(district_result))


fig, ax = plt.subplots(figsize=(10, 6))

sns.barplot(
    data=district_result.sort_values("평균불균형"),
    x="평균불균형",
    y="district",
    ax=ax
)

ax.axvline(0, linestyle="--")

ax.set_title("자치구별 평균 불균형")
ax.set_xlabel("평균 불균형")
ax.set_ylabel("자치구")

plt.tight_layout()

st.pyplot(fig)