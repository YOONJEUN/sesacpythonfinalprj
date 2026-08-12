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
from src.data.loader import RAW_DATA_DIR, PROCESSED_DATA_DIR, load_csv
from src.data.preprocessing import add_imbalance, clean_station_df, preprocess_rental_data, preprocess_station_location
from src.data.save_file import save_processed_data


st.set_page_config(page_title="서울 공공자전거 수요 불균형 분석", layout="wide", page_icon="🚲")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


comparison_period_files = {
    "불균형 합계 (25.07~26.06)": ["SeoulBikeStationUseInfo_2507to2512.csv", "SeoulBikeStationUseInfo_2601to2606.csv"],
    "불균형 합계 (24.07~25.06)": ["SeoulBikeStationUseInfo_2407to2412.csv", "SeoulBikeStationUseInfo_2501to2506.csv"],
    "불균형 합계 (23.07~24.06)": ["SeoulBikeStationUseInfo_2307to2312.csv", "SeoulBikeStationUseInfo_2401to2406.csv"],
}
comparison_station_data = {
    label: add_imbalance(clean_station_df(load_csv(files)))
    for label, files in comparison_period_files.items()
}
monthly_imbalances = {
    label: calculate_monthly_imbalance(data)
    for label, data in comparison_station_data.items()
}
monthly_rentals = {
    label: data.groupby("stat_mn", as_index=False).agg(total_rentals=("rent_cnt", "sum"))
    for label, data in comparison_station_data.items()
}

# 앱 최초 실행 시 한 번만 데이터를 로드해 session_state에 저장
def load_all_data() -> None:
    if "data_loaded" in st.session_state:
        return

    st.session_state["comparison_station_data"] = comparison_station_data
    st.session_state["data_loaded"] = True

load_all_data()

st.title("서울 공공자전거 수요 불균형 분석")

# st.caption("2025년 7월부터 2026년 6월까지의 대여소별 불균형과 2026년 4월 첫 주 이용 이력 분석")
loading_skeleton = st.skeleton(height=220)

# save_file.py에서 API 데이터를 CSV로 저장한 뒤, 여기서는 저장된 파일만 읽기
# rental_file_path = RAW_DATA_DIR / "SeoulBikeRental_20260401_7days.csv"
# station_file_path = RAW_DATA_DIR / "SeoulBikeStationMaster.csv"
# 데이터 읽어오기
# raw_rental_df = load_csv(rental_file_path.name, data_dir=RAW_DATA_DIR)
# raw_station_df = load_csv(station_file_path.name, data_dir=RAW_DATA_DIR)
# 데이터 전처리하기
# rental_df = preprocess_rental_data(raw_rental_df)
# station_df = preprocess_station_location(raw_station_df)
# 전처리한 데이터 저장하기
# save_processed_data(rental_df, "SeoulBikeRental_20260401_7days_processed.csv")
# save_processed_data(station_df, "SeoulBikeStationMaster_processed.csv")

rental_df = load_csv("SeoulBikeRental_20260401_7days_processed.csv", PROCESSED_DATA_DIR)
station_df = load_csv("SeoulBikeStationMaster_processed.csv", PROCESSED_DATA_DIR)
rental_df["rent_dt"] = pd.to_datetime(rental_df["rent_dt"], errors="coerce")
rental_df["rtn_dt"] = pd.to_datetime(rental_df["rtn_dt"], errors="coerce")

loading_skeleton.empty()


# 체크박스 변경 시 이 함수 내부만 다시 실행해, 대시보드 전체 새로고침을 방지합니다.
@st.fragment
def render_monthly_imbalance_diagnosis() -> None:
    """월별 불균형 진단 영역만 독립적으로 화면에 그립니다."""
    with st.container(border=True):
        st.header("1. 월별 대여·반납 불균형 진단")
        st.subheader("절대값 불균형 합계")

        # 7월부터 다음 해 6월까지의 월 순서와 x축 위치를 지정합니다.
        month_labels = ["7월", "8월", "9월", "10월", "11월", "12월", "1월", "2월", "3월", "4월", "5월", "6월"]
        month_positions = list(range(len(month_labels)))

        # 기간별 선 그래프 색상을 고정해 필터를 바꿔도 색상 의미가 유지되게 합니다.
        line_colors = {
            "불균형 합계 (25.07~26.06)": "#356FA8",
            "불균형 합계 (24.07~25.06)": "#D9873D",
            "불균형 합계 (23.07~24.06)": "#7A5AA6",
        }

        # 좌측은 필터, 우측은 그래프로 구성하고 그래프에 더 넓은 공간을 배정합니다.
        filter_column, chart_column = st.columns([2, 8], vertical_alignment="center")
        with filter_column:
            with st.container(border=True):
                st.markdown("##### 필터링 조건")
                st.caption("그래프에 표시할 비교 기간을 선택하세요.")

                # 체크된 기간만 그래프 선과 범례에 표시합니다.
                selected_periods = [
                    period for period in comparison_period_files
                    if st.checkbox(period.replace("불균형 합계 ", ""), value=True, key=f"monthly_imbalance_{period}")
                ]
        with chart_column:
            if not selected_periods:
                st.info("왼쪽에서 표시할 기간을 하나 이상 선택해주세요.")
                return

            # 선택한 기간의 대여 건수만 평균 내어, 막대그래프에도 필터 조건을 반영합니다.
            selected_average_rentals = pd.concat(
                [
                    monthly_rentals[period]
                    .sort_values("stat_mn")["total_rentals"]
                    .reset_index(drop=True)
                    for period in selected_periods
                ],
                axis=1,
            ).mean(axis=1)

            # 좌측 y축은 불균형 합계(선), 우측 y축은 전체 대여 건수 평균(막대)입니다.
            fig, axis = plt.subplots(figsize=(10, 4))
            rental_axis = axis.twinx()
            average_rental_bars = rental_axis.bar(month_positions, selected_average_rentals, color="#4B9B70", alpha=0.35, width=0.6, zorder=1)
            imbalance_lines = []
            for period in selected_periods:
                # 사용자가 선택한 기간의 월별 불균형 합계만 선 그래프로 추가합니다.
                line_data = monthly_imbalances[period].sort_values("stat_mn")
                line, = axis.plot(month_positions, line_data["imbalance_abs_sum"], marker="o", color=line_colors[period], label=period, zorder=3)
                imbalance_lines.append(line)
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
            rental_axis.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{x / 10000:,.0f}만"))
            rental_axis.set_ylabel("전체 대여 건수 (만 건)")
            rental_axis.tick_params(axis="y", labelcolor="#4B9B70")
            axis.legend([average_rental_bars, *imbalance_lines], ["선택 기간 전체 대여 건수 평균", *selected_periods], loc="upper left", bbox_to_anchor=(0.28, 1.02))
            fig.subplots_adjust(top=0.82)
            st.pyplot(fig, clear_figure=True)

            # # 버튼 클릭 시에만 OpenAI API를 호출해 그래프 수치 기반 인사이트를 생성합니다.
            # if st.button("AI 그래프 인사이트 생성", key="monthly_imbalance_insight_button"):
            #     try:
            #         with st.spinner("그래프 데이터를 분석하고 있습니다..."):
            #             # 생성 결과는 세션에 저장해 다음 화면 갱신에도 유지합니다.
            #             st.session_state["monthly_imbalance_insight"] = generate_monthly_imbalance_insight(
            #                 monthly_imbalances,
            #                 average_rentals,
            #                 month_labels,
            #                 selected_periods,
            #             )
            #     except Exception as error:
            #         st.error(f"AI 인사이트 생성 중 오류가 발생했습니다: {error}")

            # # 이미 생성된 인사이트가 있으면 그래프 아래 카드에 표시합니다.
            # if insight := st.session_state.get("monthly_imbalance_insight"):
            #     with st.container(border=True):
            #         st.markdown("##### AI 그래프 인사이트")
            #         st.markdown(insight)

# fragment 함수를 호출해 월별 불균형 진단 영역을 표시합니다.
render_monthly_imbalance_diagnosis()


# 2. 2026년 4월
with st.container(border=True):
    st.header("2. 2026년 4월 분석")
    st.subheader("4월 첫째 주 대여소별 평균 수요 불균형 지수")
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
    ax.axvspan(7, 9, color="#E8EEF5", alpha=0.6, label="출근 시간대")
    ax.axvspan(17, 19, color="#F9E9DB", alpha=0.6, label="퇴근 시간대")
    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("평균 수요 불균형 지수")
    ax.set_title("시간대별 평균 수요 불균형 지수")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    st.subheader("평일·주말 시간대 평균 수요 불균형 패턴")
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
    ax.axvspan(17, 19, color="#F9E9DB", alpha=0.6, label="퇴근 시간대")
    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("평균 수요 불균형 지수 (대여 - 반납)")
    ax.set_title("평일·주말 시간대 평균 수요 불균형 패턴")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)


    # c1, c2 = st.columns(2)
    # with c1:
    #     hourly_use_statistics = make_group_statistics(rental_df)["rent_hour"]
    #     st.subheader("시간대별 평균 이용 시간")
    #     st.write("출근 시간대에 짧고 빠른 이동이 집중되는지, 낮 시간대에 이용시간이 길어지는지 확인합니다.")
    #     st.pyplot(
    #         create_bar_chart(
    #             hourly_use_statistics,
    #             "rent_hour",
    #             "avg_use_min",
    #             "시간대별 평균 이용 시간",
    #             "#D9873D",
    #             x_label="대여 시간대",
    #             y_label="평균 이용 시간(분)",
    #         ),
    #         clear_figure=True,
    #     )
    # with c2:
    #     st.subheader("시간대별 평균 이용 거리")
    #     st.write("시간대별 이동 거리 차이를 통해 출퇴근·여가 이동의 특성을 함께 해석할 수 있습니다.")
    #     st.pyplot(
    #         create_bar_chart(
    #             hourly_use_statistics,
    #             "rent_hour",
    #             "avg_use_dst",
    #             "시간대별 평균 이용 거리",
    #             "#4B9B70",
    #             x_label="대여 시간대",
    #             y_label="평균 이용 거리(m)",
    #         ),
    #         clear_figure=True,
    #     )


    # c1, c2 = st.columns(2)
    # duration_imbalance = calculate_average_station_imbalance_by_bins(
    #     rental_df,
    #     feature="use_min",
    #     bins=[0, 10, 20, 30, 60, 120, float("inf")],
    #     labels=["0~10분", "10~20분", "20~30분", "30~60분", "60~120분", "120분 이상"],
    # )
    # with c1:
    #     st.subheader("이용시간별 대여소 평균 절대 수요 불균형 지수")
    #     st.write("상쇄되어 평균이 0이 되는 것을 피하기 위해, 이용시간 구간별 대여소 불균형의 절댓값을 평균냈습니다.")
    #     fig, ax = plt.subplots(figsize=(12, 6))
    #     ax.plot(duration_imbalance["feature_group"].astype(str), duration_imbalance["average_absolute_imbalance"], marker="o", color="#D9873D", linewidth=2)
    #     ax.set_xlabel("이용시간")
    #     ax.set_ylabel("평균 절대 수요 불균형 지수")
    #     ax.set_title("이용시간별 대여소 평균 절대 수요 불균형 지수")
    #     ax.grid(axis="y", alpha=0.3)
    #     fig.tight_layout()
    #     st.pyplot(fig, clear_figure=True)

    # distance_imbalance = calculate_average_station_imbalance_by_bins(
    #     rental_df,
    #     feature="use_dst",
    #     bins=[0, 1_000, 2_000, 3_000, 5_000, 10_000, float("inf")],
    #     labels=["0~1km", "1~2km", "2~3km", "3~5km", "5~10km", "10km 이상"],
    # )
    # with c2:
    #     st.subheader("이용 거리별 대여소 평균 절대 수요 불균형 지수")
    #     st.write("상쇄되어 평균이 0이 되는 것을 피하기 위해, 이용거리 구간별 대여소 불균형의 절댓값을 평균냈습니다.")
    #     fig, ax = plt.subplots(figsize=(12, 6))
    #     ax.plot(distance_imbalance["feature_group"].astype(str), distance_imbalance["average_absolute_imbalance"], marker="o", color="#4B9B70", linewidth=2)
    #     ax.set_xlabel("이용 거리")
    #     ax.set_ylabel("평균 절대 수요 불균형 지수")
    #     ax.set_title("이용 거리별 대여소 평균 절대 수요 불균형 지수")
    #     ax.grid(axis="y", alpha=0.3)
    #     fig.tight_layout()
    #     st.pyplot(fig, clear_figure=True)


# 3. 대여소 유형별 시간대 불균형
with st.container(border=True):
    st.header("3. 대여소 유형별 시간대 불균형")

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


# 4. 출퇴근 시간대 재배치 우선순위
with st.container(border=True):
    st.header("4. 출퇴근 시간대 재배치 우선순위")
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
