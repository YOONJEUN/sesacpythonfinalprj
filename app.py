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
sns.set_theme(style="whitegrid", palette="deep")

plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

st.title("서울 공공자전거 수요 불균형 분석")
st.caption("따릉이의 대여 및 반납 불균형을 분석하여 자전거 재배치 우선순위 결정")

# loading_skeleton = st.skeleton(height=220)

categorized_rentals = load_parquet("SeoulBikeRental_20260401_7days_station_categories.parquet", PROCESSED_DATA_DIR)
hourly_category_imbalance = calculate_hourly_category_imbalance(categorized_rentals)
commute_priority, _ = calculate_commute_station_priorities(categorized_rentals)


# 대여소 유형별 리스트
category_options = hourly_category_imbalance["category"].drop_duplicates().tolist()

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


station_df = load_csv("SeoulBikeStationMaster_processed.csv", PROCESSED_DATA_DIR)
rental_df = load_parquet("SeoulBikeRental_20260401_7days_processed.parquet", PROCESSED_DATA_DIR)

rental_df["rent_dt"] = pd.to_datetime(rental_df["rent_dt"], errors="coerce")
rental_df["rtn_dt"] = pd.to_datetime(rental_df["rtn_dt"], errors="coerce")

# loading_skeleton.empty()



# 필터링 조건이 있는 곳
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

# KPI 
col1, col2, col3, col4 = st.columns(4)
with col1:
    with st.container(border=True):
        st.subheader("첫 번째")
        st.write("첫 번째 내용")

with col2:
    with st.container(border=True):
        st.subheader("두 번째")
        st.write("두 번째 내용")

with col3:
    with st.container(border=True):
        st.subheader("세 번째")
        st.write("세 번째 내용")

with col4:
    with st.container(border=True):
        st.subheader("네 번째")
        st.write("네 번째 내용")


col1, col2 = st.columns("")
with col1:
    with st.container(border=True):
        st.subheader("1번 그래프")
        st.write("1번 그래프")

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
        st.subheader("3번 그래프")
        st.write("3번 그래프")

with col2:
    with st.container(border=True):
        st.subheader("4번 그래프")
        st.write("4번 그래프")


# 대여소 유형별 시간대 불균형
with st.container(border=True):
    st.header("대여소 유형별 시간대 불균형")
        
    




# 4. 출퇴근 시간대 재배치 우선순위
with st.container(border=True):
    st.header("재배치 우선순위")

    # 4번 그래프의 필터와 결과를 fragment로 묶어, 필터 변경 시 이 영역만 갱신합니다.
    @st.fragment
    def render_commute_priority_chart() -> None:
        filter_column, chart_column = st.columns([2, 8], vertical_alignment="top")
        with filter_column:
            with st.container(border=True):
                st.markdown("##### 필터링 조건")
                top_station_count = st.slider(
                    "표시할 상위 대여소 수",
                    min_value=10,
                    max_value=30,
                    value=15,
                    step=5,
                    key="commute_priority_top_station_count",
                )

        with chart_column:
            st.pyplot(
                create_commute_priority_bubble_chart(commute_priority, top_station_count),
                clear_figure=True,
            )
            st.dataframe(
                commute_priority.head(top_station_count),
                column_config={
                    "priority_rank": "우선순위",
                    "station_id": "대여소 ID",
                    "station_name": "대여소명",
                    "category": "유형",
                    "morning_imbalance": "오전 불균형",
                    "evening_imbalance": "오후 불균형",
                    "commute_priority": "재배치 우선순위",
                    "net_imbalance": "순불균형",
                    "recommended_action": "권장 조치",
                },
                hide_index=True,
            )

    render_commute_priority_chart()
