"""서울 공공자전거 수요 불균형 및 재배치 분석 Streamlit 대시보드."""

import math
import pandas as pd

import koreanize_matplotlib  # noqa: F401 - matplotlib 한글 폰트 설정
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import matplotlib.ticker as mticker

from src.analysis.analysis import (
    calculate_average_station_imbalance_by_bins,
    calculate_hourly_returns,
    calculate_weekday_hourly_imbalance,
    calculate_weektype_hourly_average_imbalance,
    calculate_weekly_average_station_hourly_imbalance,
    calculate_monthly_imbalance,
    calculate_station_rebalancing,
    calculate_top_routes,
    create_bar_chart,
    make_group_statistics,
    create_commute_priority_bar_chart
)
from src.analysis.station_category import (
    add_station_categories,
    calculate_commute_station_priorities,
    calculate_hourly_category_imbalance,
    create_commute_priority_bubble_chart,
    create_hourly_category_imbalance_chart,
)
from src.api.openai_api import generate_monthly_imbalance_insight
from src.data.loader import RAW_DATA_DIR, PROCESSED_DATA_DIR, load_csv, load_parquet
from src.data.preprocessing import add_imbalance, clean_station_df, preprocess_rental_data, preprocess_station_location
from src.data.save_file import save_processed_data

st.set_page_config(page_title="서울 공공자전거 수요 불균형 분석", layout="wide", page_icon="🚲")
st.markdown("""
<style>
    .block-container {
        max-width: 100%;
        padding-top: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

sns.set_theme(style="whitegrid", palette="deep")

plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

st.title("서울 공공자전거 수요 불균형 분석")
st.caption("따릉이의 대여 및 반납 불균형을 분석하여 자전거 재배치 우선순위 결정")


# '전체' 체크박스 변경 시 모든 대여소 유형 체크박스 상태를 함께 변경합니다.
def toggle_all_station_categories() -> None:
    select_all = st.session_state["station_category_all"]
    for category in category_options:
        st.session_state[f"station_category_{category}"] = select_all

# 개별 유형을 조절하면 '전체' 체크박스 상태도 현재 선택 결과에 맞춰 갱신합니다.
def sync_all_station_categories() -> None:
    st.session_state["station_category_all"] = all(
        st.session_state.get(f"station_category_{category}", True)
        for category in category_options
)

# 지도용
# station_df = load_csv("SeoulBikeStationMaster_processed.csv", PROCESSED_DATA_DIR)

# ============================================
# 데이터 로드
# ============================================
categorized_rentals = load_parquet("SeoulBikeRental_20260401_7days_station_categories.parquet", PROCESSED_DATA_DIR)
rental_df = categorized_rentals.copy()
rental_df["rent_dt"] = pd.to_datetime(rental_df["rent_dt"], errors="coerce")
rental_df["rtn_dt"] = pd.to_datetime(rental_df["rtn_dt"], errors="coerce")

hourly_category_imbalance = calculate_hourly_category_imbalance(categorized_rentals)

# 대여소 유형별 리스트
category_options = hourly_category_imbalance["category"].drop_duplicates().tolist()

# ============================================
# 필터
# ============================================
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container():
            # 현재는 하드코딩 >
            st.selectbox("날짜", ["2026-04-01 ~ 2026-04-08"])

    with col2:
        with st.container():
            selected_category = st.selectbox("대여소 유형", ["전체"] + category_options,)
            if selected_category == "전체":
                selected_categories = category_options
            else:
                selected_categories = [selected_category]

# commute_priority, _ = calculate_commute_station_priorities(categorized_rentals)
commute_priority, commute_hourly = (
    calculate_commute_station_priorities(
        categorized_rentals,
        selected_category=selected_category,
    )
)

if selected_category == "전체":
    filtered_categorized_rentals = categorized_rentals.copy()
else:
    filtered_categorized_rentals = categorized_rentals[
        categorized_rentals["rent_category"].eq(selected_category)
        | categorized_rentals["rtn_category"].eq(selected_category)
    ].copy()




# 대여소별 재배치 우선순위 계산
station_rebalancing = calculate_station_rebalancing(rental_df, selected_categories)

# ============================================
# KPI
# ============================================
# 1. 총 대여 건수
total_rentals = rental_df.loc[
    rental_df["rent_category"].isin(selected_categories)
].shape[0]

# 2. 총 반납 건수
total_returns = rental_df.loc[
    rental_df["rtn_category"].isin(selected_categories)
    & rental_df["rtn_dt"].notna()
].shape[0]

# 3. 전체 대여소의 불균형 절대값 합계
total_imbalance_abs = station_rebalancing["rebalancing_priority"].sum()

# 4. 불균형이 가장 큰 상위 10% 대여소 수
if station_rebalancing.empty:
    urgent_station_count = 0
else:
    priority_threshold = (
        station_rebalancing["rebalancing_priority"]
        .quantile(0.95)
    )

    urgent_station_count = (
        station_rebalancing["rebalancing_priority"]
        >= priority_threshold
    ).sum()

# ============================================
# 시간대별 평균 불균형
# ============================================
weekly_average_imbalance = calculate_weekly_average_station_hourly_imbalance(rental_df, selected_categories)

# KPI 
col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.metric(
            label="🚲 총 대여 건수",
            value=f"{total_rentals:,}건",
        )

with col2:
    with st.container(border=True):
        st.metric(
            label="총 반납 건수",
            value=f"{total_returns:,}건",
        )

with col3:
    with st.container(border=True):
        st.metric(
            label="총 불균형 절대값",
            value=f"{total_imbalance_abs:,}건",
        )

with col4:
    with st.container(border=True):
        st.metric(
            label="재배치 필요 대여소",
            value=f"{urgent_station_count:,}개소",
        )



col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.caption("시간대별 평균 수요 불균형 지수")
        fig, ax = plt.subplots(figsize=(13, 6))
        ax.plot(
            weekly_average_imbalance["hour"],
            weekly_average_imbalance["average_imbalance"],
            marker="o",
            color="#356FA8",
            linewidth=2,
        )
        ax.fill_between(
            weekly_average_imbalance["hour"],
            weekly_average_imbalance["average_imbalance"],
            0,
            where=weekly_average_imbalance["average_imbalance"].ge(0),
            color="#356FA8",
            alpha=0.2,
            interpolate=True,
        )
        ax.fill_between(
            weekly_average_imbalance["hour"],
            weekly_average_imbalance["average_imbalance"],
            0,
            where=weekly_average_imbalance["average_imbalance"].lt(0),
            color="#C9534B",
            alpha=0.2,
            interpolate=True,
        )
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.axvspan(7, 9, color="#E8EEF5", alpha=0.6, label="출근 시간대")
        ax.axvspan(17, 19, color="#F9E9DB", alpha=0.6, label="퇴근 시간대")
        ax.set_xticks(range(24))
        ax.set_xlabel("시간대")
        ax.set_ylabel("평균 수요 불균형 지수")
        ax.set_title("시간대별 평균 수요 불균형 지수")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

with col2:
    with st.container(border=True):
        st.caption("대여소 유형별 시간대 불균형 추이")
        @st.fragment
        def render_hourly_category_imbalance_chart() -> None:
            if not selected_categories:
                st.info("왼쪽에서 표시할 대여소 유형을 하나 이상 선택해주세요.")
            else:
                st.pyplot(
                    create_hourly_category_imbalance_chart(
                        hourly_category_imbalance,
                        selected_categories,
                    ),
                    clear_figure=True,
                )
        
        render_hourly_category_imbalance_chart()

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.caption("재배치 우선순위")

        if commute_priority.empty:
            st.info(
                "선택한 대여소 유형은 현재 출퇴근 우선순위 분석 대상이 아닙니다."
            )
        else:
            # 4번 그래프의 필터와 결과를 fragment로 묶어, 필터 변경 시 이 영역만 갱신합니다.
            @st.fragment
            def render_commute_priority_chart() -> None:
                
                st.pyplot(
                    create_commute_priority_bubble_chart(commute_priority),
                    clear_figure=True,
                )
                
        render_commute_priority_chart()

with col2:
    with st.container(border=True):
        if commute_priority.empty:
            st.info(
                "선택한 대여소 유형은 현재 출퇴근 우선순위 분석 대상이 아닙니다."
            )
        else:
            st.pyplot(
                create_commute_priority_bar_chart(
                    commute_priority,
                    top_n=20,
                ),
                clear_figure=True,
            )

with st.container(border=True):
    display_df = commute_priority.head(15).drop(
        columns="commute_priority"
    )
    st.dataframe(
        display_df,
        column_config={
            "priority_rank": "우선순위",
            "station_id": "대여소 ID",
            "station_name": "대여소명",
            "category": "유형",
            "morning_imbalance": "오전 불균형",
            "evening_imbalance": "오후 불균형",
            # "commute_priority": "재배치 우선순위",
            "net_imbalance": "순불균형",
            "recommended_action": "권장 조치",
        },
        hide_index=True,
    )



    
