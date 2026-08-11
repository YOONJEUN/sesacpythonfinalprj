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



# 2. 2026년 4월
with st.container(border=True):
    st.header("2. 2026년 4월 분석")
    st.subheader("4월 첫째 주 대여소별 평균 수요 불균형 지수")
    st.write("4월 1~7일의 모든 대여소·시간대 불균형 지수를 평균냈으며, 이용 기록이 없는 시간대는 0으로 포함했습니다.")
    weekly_average_imbalance = calculate_weekly_average_station_hourly_imbalance(rental_df)

    fig, ax = plt.subplots(figsize=(12, 4.5))
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
    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("평균 수요 불균형 지수")
    ax.set_title("대여소별 평균 수요 불균형 지수 (2026년 4월 1일~7일)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    st.subheader("평일·주말 시간대 평균 수요 불균형 패턴")
    st.write("월~금과 토~일을 각각 묶어, 각 시간대 수요 불균형 지수의 평균을 비교합니다.")
    weekday_hourly_imbalance = calculate_weekday_hourly_imbalance(rental_df)
    weektype_hourly_imbalance = calculate_weektype_hourly_average_imbalance(weekday_hourly_imbalance)
    fig, ax = plt.subplots(figsize=(12, 5))
    for day_type, color, linestyle in [("평일 (월~금)", "#356FA8", "-"), ("주말 (토~일)", "#C9534B", "--")]:
        data = weektype_hourly_imbalance.loc[weektype_hourly_imbalance["day_type"].eq(day_type)]
        ax.plot(
            data["hour"],
            data["average_imbalance"],
            label=day_type,
            color=color,
            linewidth=2.4,
            linestyle=linestyle,
        )
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.axvspan(7, 9, color="#E8EEF5", alpha=0.6, label="출근 시간대")
    ax.axvspan(18, 20, color="#F9E9DB", alpha=0.6, label="퇴근 시간대")
    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("평균 수요 불균형 지수 (대여 - 반납)")
    ax.set_title("평일·주말 시간대 평균 수요 불균형 패턴")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)


    c1, c2 = st.columns(2)
    with c1:
        hourly_use_statistics = make_group_statistics(rental_df)["rent_hour"]
        st.subheader("시간대별 평균 이용 시간")
        st.write("출근 시간대에 짧고 빠른 이동이 집중되는지, 낮 시간대에 이용시간이 길어지는지 확인합니다.")
        st.pyplot(
            create_bar_chart(hourly_use_statistics, "rent_hour", "avg_use_min", "시간대별 평균 이용 시간", "#D9873D"),
            clear_figure=True,
        )
    with c2:
        st.subheader("시간대별 평균 이용 거리")
        st.write("시간대별 이동 거리 차이를 통해 출퇴근·여가 이동의 특성을 함께 해석할 수 있습니다.")
        st.pyplot(
            create_bar_chart(hourly_use_statistics, "rent_hour", "avg_use_dst", "시간대별 평균 이용 거리", "#4B9B70"),
            clear_figure=True,
        )


    c1, c2 = st.columns(2)
    duration_imbalance = calculate_average_station_imbalance_by_bins(
        rental_df,
        feature="use_min",
        bins=[0, 10, 20, 30, 60, 120, float("inf")],
        labels=["0~10분", "10~20분", "20~30분", "30~60분", "60~120분", "120분 이상"],
    )
    with c1:
        st.subheader("이용시간별 대여소 평균 절대 수요 불균형 지수")
        st.write("상쇄되어 평균이 0이 되는 것을 피하기 위해, 이용시간 구간별 대여소 불균형의 절댓값을 평균냈습니다.")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(duration_imbalance["feature_group"].astype(str), duration_imbalance["average_absolute_imbalance"], marker="o", color="#D9873D", linewidth=2)
        ax.set_xlabel("이용시간")
        ax.set_ylabel("평균 절대 수요 불균형 지수")
        ax.set_title("이용시간별 대여소 평균 절대 수요 불균형 지수")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

    distance_imbalance = calculate_average_station_imbalance_by_bins(
        rental_df,
        feature="use_dst",
        bins=[0, 1_000, 2_000, 3_000, 5_000, 10_000, float("inf")],
        labels=["0~1km", "1~2km", "2~3km", "3~5km", "5~10km", "10km 이상"],
    )
    with c2:
        st.subheader("이용 거리별 대여소 평균 절대 수요 불균형 지수")
        st.write("상쇄되어 평균이 0이 되는 것을 피하기 위해, 이용거리 구간별 대여소 불균형의 절댓값을 평균냈습니다.")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(distance_imbalance["feature_group"].astype(str), distance_imbalance["average_absolute_imbalance"], marker="o", color="#4B9B70", linewidth=2)
        ax.set_xlabel("이용 거리")
        ax.set_ylabel("평균 절대 수요 불균형 지수")
        ax.set_title("이용 거리별 대여소 평균 절대 수요 불균형 지수")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)


# 4. 대여소 유형별 시간대 불균형
with st.container(border=True):
    st.header("4. 대여소 유형별 시간대 불균형")
    st.write(
        "대여소명에 포함된 시설 키워드를 바탕으로 유형을 분류했습니다. "
        "불균형 수치는 7일간 유형별 시간대 대여 건수에서 반납 건수를 뺀 값입니다."
    )

    categorized_rentals = add_station_categories(rental_df)
    output_filename = "SeoulBikeRental_20260401_7days_station_categories.csv"
    output_path = PROCESSED_DATA_DIR / output_filename
    if not output_path.exists():
        save_processed_data(categorized_rentals, output_filename)

    hourly_category_imbalance = calculate_hourly_category_imbalance(categorized_rentals)
    st.pyplot(create_hourly_category_imbalance_chart(hourly_category_imbalance), clear_figure=True)

    # st.subheader("유형별 요약")
    # category_summary = hourly_category_imbalance.groupby("category", as_index=False).agg(
    #     total_imbalance=("imbalance", "sum"),
    #     hourly_peak_abs_imbalance=("imbalance", lambda values: values.abs().max()),
    # )
    # st.dataframe(category_summary, hide_index=True, use_container_width=True)


# 5. 출퇴근 시간대 재배치 우선순위
with st.container(border=True):
    st.header("5. 출퇴근 시간대 재배치 우선순위")
    st.write(
        "지하철/버스·주거지·회사 유형 중 오전 7-9시와 오후 17-19시의 불균형이 큰 대여소를 추렸습니다. "
        "우선순위는 각 시간대 순불균형의 절댓값 합으로 계산합니다. 양수는 자전거 공급, 음수는 자전거 회수가 필요한 상태입니다."
    )

    commute_priority, _ = calculate_commute_station_priorities(categorized_rentals)
    top_station_count = st.slider("표시할 상위 대여소 수", min_value=10, max_value=30, value=15, step=5)

    st.pyplot(create_commute_priority_bubble_chart(commute_priority, top_station_count), clear_figure=True)

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
        use_container_width=True,
    )
