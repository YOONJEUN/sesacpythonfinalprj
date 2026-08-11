"""서울 공공자전거 수요 불균형 및 재배치 분석 Streamlit 대시보드."""

import math
import pandas as pd

import koreanize_matplotlib  # noqa: F401 - matplotlib 한글 폰트 설정
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import matplotlib.ticker as mticker

from src.analysis.analysis import (
    calculate_gender_mix,
    calculate_hourly_returns,
    calculate_daily_station_hourly_imbalance,
    calculate_monthly_imbalance,
    calculate_station_rebalancing,
    calculate_top_routes,
    create_bar_chart,
    make_group_statistics,
)
from src.data.loader import RAW_DATA_DIR, PROCESSED_DATA_DIR, load_csv
from src.data.preprocessing import add_imbalance, clean_station_df, preprocess_rental_data, preprocess_station_location
from src.data.save_file import save_processed_data


st.set_page_config(page_title="서울 공공자전거 수요 불균형 분석", layout="wide", page_icon="🚲")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


current_station_files = ["SeoulBikeStationUseInfo_2507to2512.csv", "SeoulBikeStationUseInfo_2601to2606.csv"]
previous_station_files = ["SeoulBikeStationUseInfo_2407to2412.csv", "SeoulBikeStationUseInfo_2501to2506.csv"]
current_station_df = add_imbalance(clean_station_df(load_csv(current_station_files)))
previous_station_df = add_imbalance(clean_station_df(load_csv(previous_station_files)))
current_monthly_imbalance = calculate_monthly_imbalance(current_station_df)
previous_monthly_imbalance = calculate_monthly_imbalance(previous_station_df)
# 각 대여소의 월별 대여 건수(rent_cnt) 더하기
current_monthly_rentals = current_station_df.groupby("stat_mn", as_index=False).agg(total_rentals=("rent_cnt", "sum"))
previous_monthly_rentals = previous_station_df.groupby("stat_mn", as_index=False).agg(total_rentals=("rent_cnt", "sum"))

# 앱 최초 실행 시 한 번만 데이터를 로드해 session_state에 저장
def load_all_data() -> None:
    if "data_loaded" in st.session_state:
        return

    current_station_df = add_imbalance(clean_station_df(load_csv(current_station_files)))
    previous_station_df = add_imbalance(clean_station_df(load_csv(previous_station_files)))

    st.session_state["current_station_df"] = current_station_df
    st.session_state["previous_station_df"] = previous_station_df
    st.session_state["data_loaded"] = True

load_all_data()

st.title("서울 공공자전거 수요 불균형 분석")
# st.caption("2025년 7월부터 2026년 6월까지의 대여소별 불균형과 2026년 4월 첫 주 이용 이력 분석")
loading_skeleton = st.skeleton(height=220)

# save_file.py에서 API 데이터를 CSV로 저장한 뒤, 여기서는 저장된 파일만 읽기
rental_file_path = RAW_DATA_DIR / "SeoulBikeRental_20260401_7days.csv"
station_file_path = RAW_DATA_DIR / "SeoulBikeStationMaster.csv"
# 데이터 읽어오기
raw_rental_df = load_csv(rental_file_path.name, data_dir=RAW_DATA_DIR)
raw_station_df = load_csv(station_file_path.name, data_dir=RAW_DATA_DIR)
# 데이터 전처리하기
rental_df = preprocess_rental_data(raw_rental_df)
station_df = preprocess_station_location(raw_station_df)
# 전처리한 데이터 저장하기
save_processed_data(rental_df, "SeoulBikeRental_20260401_7days_processed.csv")
save_processed_data(station_df, "SeoulBikeStationMaster_processed.csv")





loading_skeleton.empty()




# 1. 월별 대여·반납 불균형 진단
with st.container(border=True):
    st.header("1. 월별 대여·반납 불균형 진단")
    st.write("불균형 절대값 합계가 클수록 대여소별 대여·반납 차이가 커서 재배치 운영을 우선 검토해야 하는 달이라는 것을 유추 가능")

    c1, c2, c3 = st.columns(3)
    c1.metric("ㅁㄴㅇ", f"123123")
    c2.metric("1234", f"123123")
    c3.metric("ㅑㅐㅣㅐㅑ", f"123")

    st.subheader("절대값 불균형 합계")
    current_line_data = current_monthly_imbalance.sort_values("stat_mn").copy()
    previous_line_data = previous_monthly_imbalance.sort_values("stat_mn").copy()
    current_rental_line_data = current_monthly_rentals.sort_values("stat_mn").copy()
    previous_rental_line_data = previous_monthly_rentals.sort_values("stat_mn").copy()
    month_labels = ["7월", "8월", "9월", "10월", "11월", "12월", "1월", "2월", "3월", "4월", "5월", "6월"]
    month_positions = list(range(len(month_labels)))
    average_rentals = (current_rental_line_data["total_rentals"].reset_index(drop=True) + previous_rental_line_data["total_rentals"].reset_index(drop=True)) / 2
    
    fig, axis = plt.subplots(figsize=(10, 4))

    rental_axis = axis.twinx()
    average_rental_bars = rental_axis.bar(
        month_positions,
        average_rentals,
        color="#4B9B70",
        alpha=0.35,
        width=0.6,
        label="전체 대여 건수 2년 평균",
        zorder=1,
    )
    current_imbalance_line, = axis.plot(
        month_positions,
        current_line_data["imbalance_abs_sum"],
        marker="o",
        color="#356FA8",
        label="2025년 7월 ~ 2026년 6월",
        zorder=3,
    )
    previous_imbalance_line, = axis.plot(
        month_positions,
        previous_line_data["imbalance_abs_sum"],
        marker="o",
        color="#D9873D",
        label="2024년 7월 ~ 2025년 6월",
        zorder=3,
    )

    axis.patch.set_visible(False)
    rental_axis.patch.set_visible(True)

    axis.set_zorder(rental_axis.get_zorder() + 1)

    axis.set_xlim(-0.25, len(month_labels) - 0.75)
    axis.set_ylim(bottom=130_000)
    axis.set_xticks(month_positions, month_labels)
    axis.set_xlabel("월별")
    axis.set_ylabel("불균형 절대값 합계")
    axis.tick_params(axis="y", labelcolor="#356FA8")
    axis.set_title("월별 불균형 합계와 전체 대여 건수 추이 비교")
    axis.grid(axis="y", alpha=0.3)
    
    rental_axis.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, pos: f"{x/10000:,.0f}만")
    )
    rental_axis.set_ylabel("전체 대여 건수 (만 건)")
    rental_axis.tick_params(axis="y", labelcolor="#4B9B70")
    
    axis.legend(
        [average_rental_bars , previous_imbalance_line, current_imbalance_line],
        [
            "전체 대여 건수 2년 평균",
            "불균형 합계 (25.07~26.06)",
            "불균형 합계 (24.07~25.06)",
        ],
        loc="upper left",
        bbox_to_anchor=(0.4, 1.02),
    )
    fig.subplots_adjust(top=0.82)
    st.pyplot(fig, clear_figure=True)



# 1-1. 따릉이 불균형 지수
with st.container(border=True):
    st.header("1-1. 따릉이 불균형 지수")
    combined_station_df = pd.concat([current_station_df, previous_station_df], ignore_index=True)
    station_name, station_id, hourly_imbalance = calculate_daily_station_hourly_imbalance(
        combined_station_df,
        rental_df,
        target_date="2026-04-01",
    )
    st.write("수요 불균형 수치가 가장 큰 대여소 한 곳을 골라 불균형 지수 확인")

    fig, ax = plt.subplots(figsize=(12, 4.5))
    colors = hourly_imbalance["imbalance"].ge(0).map({True: "#356FA8", False: "#C9534B"})
    ax.bar(hourly_imbalance["hour"], hourly_imbalance["imbalance"], color=colors, width=0.75)
    ax.axhline(0, color="#333333", linewidth=0.8)
    
    # 0이 축 정중앙에 오도록 y축 범위를 대칭으로 설정
    max_abs_imbalance = hourly_imbalance["imbalance"].abs().max()
    ax.set_ylim(-max_abs_imbalance * 1.1, max_abs_imbalance * 1.1)

    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("수요 불균형 지수")
    ax.set_title("응암역2번출구 국민은행 앞 대여소의 수요 불균형 지수 (2026년 4월 1일)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)






# 2. 이용 시간별 수요 분석
with st.container(border=True):
    st.header("2. 2026년 4월 첫 주 수요 분석")
    max_use_hour = max(1, math.ceil(rental_df["use_min"].max() / 60))
    use_hour_range = st.slider(
        "이용 시간 범위(시간)",
        0,
        max_use_hour,
        (0, max_use_hour),
        key="demand_duration",
    )
    filtered_df = rental_df[rental_df["use_min"].between(use_hour_range[0] * 60, use_hour_range[1] * 60)].copy()

    if filtered_df.empty:
        st.warning("선택한 이용 시간 범위에 해당하는 데이터가 없습니다.")
    else:
        hourly = make_group_statistics(filtered_df)["rent_hour"]
        hourly_returns = calculate_hourly_returns(filtered_df)
        c1, c2, c3 = st.columns(3)
        c1.metric("필터 적용 이용 건수", f"{len(filtered_df):,}건")
        c2.metric("평균 이용 시간", f"{filtered_df['use_min'].mean():.1f}분")
        c3.metric("평균 이용 거리", f"{filtered_df['use_dst'].mean():,.0f}m")

        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "trip_count", "시간대별 대여 건수", "#356FA8"), clear_figure=True)
        with c2:
            st.pyplot(create_bar_chart(hourly_returns, "rtn_hour", "return_count", "시간대별 반납 건수", "#4B9B70"), clear_figure=True)

        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "avg_use_min", "시간대별 평균 이용 시간", "#D9873D"), clear_figure=True)
        with c2:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "avg_use_dst", "시간대별 평균 이용 거리", "#A65D8B"), clear_figure=True)

# 3. 자전거 재배치 우선순위
with st.container(border=True):
    st.header("3. 자전거 재배치 우선순위")
    min_trip_count = st.number_input("최소 이용 건수", min_value=0, value=30, step=10, key="rebalancing_min_count")
    station_flow = calculate_station_rebalancing(rental_df)
    station_flow = station_flow[(station_flow["rentals"] + station_flow["returns"]) >= min_trip_count]
    top_routes = calculate_top_routes(rental_df)
    top_routes = top_routes[top_routes["trip_count"] >= min_trip_count]
    gender_mix = calculate_gender_mix(rental_df)

    c1, c2 = st.columns(2)
    with c1:
        st.pyplot(
            create_bar_chart(
                station_flow.nlargest(15, "net_outflow").sort_values("net_outflow"),
                "net_outflow",
                "station_name",
                "자전거 공급 우선 대여소",
                "#C9534B",
            ),
            clear_figure=True,
        )
    with c2:
        st.pyplot(
            create_bar_chart(
                station_flow.nsmallest(15, "net_outflow").sort_values("net_outflow", ascending=False),
                "net_outflow",
                "station_name",
                "자전거 회수 우선 대여소",
                "#40845D",
            ),
            clear_figure=True,
        )

    tab1, tab2, tab3 = st.tabs(["재배치 우선 대여소", "주요 이동 경로", "성별 이용 분포"])
    with tab1:
        st.dataframe(station_flow.head(30), hide_index=True, use_container_width=True)
    with tab2:
        st.dataframe(top_routes, hide_index=True, use_container_width=True)
    with tab3:
        st.pyplot(create_bar_chart(gender_mix, "sex", "trip_count", "성별 대여 건수", "#6D78AD"), clear_figure=True)
